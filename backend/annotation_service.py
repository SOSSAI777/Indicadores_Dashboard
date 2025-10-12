import json
import redis
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class AnnotationService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.annotation_key_prefix = "annotation:"
        self.user_annotations_prefix = "user_annotations:"
        self.symbol_annotations_prefix = "symbol_annotations:"
    
    def create_annotation(self, user_id: str, annotation_data: Dict) -> Dict:
        """Cria uma nova anotação"""
        try:
            annotation_id = f"anno_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            
            annotation = {
                "id": annotation_id,
                "user_id": user_id,
                "symbol": annotation_data['symbol'],
                "chart_time": annotation_data['chart_time'],
                "content": annotation_data['content'],
                "drawing_data": annotation_data.get('drawing_data', {}),
                "category": annotation_data.get('category', 'general'),
                "color": annotation_data.get('color', '#FFD700'),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            # Salva no Redis
            annotation_key = f"{self.annotation_key_prefix}{annotation_id}"
            self.redis.set(annotation_key, json.dumps(annotation))
            
            # Adiciona às listas
            self.redis.sadd(f"{self.user_annotations_prefix}{user_id}", annotation_id)
            self.redis.sadd(f"{self.symbol_annotations_prefix}{annotation_data['symbol']}", annotation_id)
            
            logger.info(f"Anotação criada: {annotation_id}")
            return annotation
            
        except Exception as e:
            logger.error(f"Erro ao criar anotação: {e}")
            return None
    
    def get_user_annotations(self, user_id: str, symbol: Optional[str] = None) -> List[Dict]:
        """Recupera anotações do usuário, opcionalmente filtradas por símbolo"""
        try:
            user_annotations_key = f"{self.user_annotations_prefix}{user_id}"
            annotation_ids = self.redis.smembers(user_annotations_key)
            
            annotations = []
            for annotation_id in annotation_ids:
                annotation_key = f"{self.annotation_key_prefix}{annotation_id.decode()}"
                annotation_data = self.redis.get(annotation_key)
                
                if annotation_data:
                    annotation = json.loads(annotation_data)
                    
                    # Filtra por símbolo se especificado
                    if symbol and annotation['symbol'] != symbol:
                        continue
                    
                    annotations.append(annotation)
            
            return sorted(annotations, key=lambda x: x['created_at'], reverse=True)
            
        except Exception as e:
            logger.error(f"Erro ao buscar anotações: {e}")
            return []
    
    def update_annotation(self, annotation_id: str, updates: Dict) -> bool:
        """Atualiza uma anotação existente"""
        try:
            annotation_key = f"{self.annotation_key_prefix}{annotation_id}"
            annotation_data = self.redis.get(annotation_key)
            
            if annotation_data:
                annotation = json.loads(annotation_data)
                annotation.update(updates)
                annotation['updated_at'] = datetime.now().isoformat()
                
                self.redis.set(annotation_key, json.dumps(annotation))
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao atualizar anotação: {e}")
            return False
    
    def delete_annotation(self, user_id: str, annotation_id: str) -> bool:
        """Remove uma anotação"""
        try:
            annotation_key = f"{self.annotation_key_prefix}{annotation_id}"
            annotation_data = self.redis.get(annotation_key)
            
            if annotation_data:
                annotation = json.loads(annotation_data)
                symbol = annotation['symbol']
                
                # Remove das listas
                self.redis.delete(annotation_key)
                self.redis.srem(f"{self.user_annotations_prefix}{user_id}", annotation_id)
                self.redis.srem(f"{self.symbol_annotations_prefix}{symbol}", annotation_id)
                
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao deletar anotação: {e}")
            return False
    
    def get_annotation_categories(self, user_id: str) -> List[str]:
        """Recupera categorias únicas do usuário"""
        annotations = self.get_user_annotations(user_id)
        categories = set(annotation['category'] for annotation in annotations)
        return sorted(list(categories))

# Instância global (será inicializada no main.py)
annotation_service = None