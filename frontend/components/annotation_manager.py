import streamlit as st
import json
from datetime import datetime
import plotly.graph_objects as go

class AnnotationManager:
    def __init__(self):
        self.user_id = "default_user"
        self.categories = ["geral", "compra", "venda", "alvo", "suporte", "resistência"]
    
    def render_annotation_panel(self, current_symbol=None):
        """Renderiza painel de anotações"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("📝 Anotações")
        
        # Criar nova anotação
        with st.sidebar.expander("✏️ Nova Anotação", expanded=False):
            self.render_annotation_creator(current_symbol)
        
        # Lista de anotações
        st.sidebar.subheader("Anotações Salvas")
        self.render_saved_annotations(current_symbol)
    
    def render_annotation_creator(self, current_symbol=None):
        """Interface para criar novas anotações"""
        symbol = st.text_input("Símbolo", value=current_symbol or "AAPL", key="anno_symbol")
        content = st.text_area("Conteúdo da Anotação", placeholder="Digite suas observações...")
        
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("Categoria", options=self.categories)
        with col2:
            color = st.color_picker("Cor", value="#FFD700")
        
        # Dados de desenho (simplificado)
        drawing_data = {
            "type": "text",
            "x": datetime.now().timestamp(),
            "y": 100.0,  # Posição Y no gráfico
            "color": color
        }
        
        if st.button("Salvar Anotação", type="primary"):
            if content and symbol:
                if self.create_annotation(symbol, content, category, color, drawing_data):
                    st.success("✅ Anotação salva!")
                else:
                    st.error("❌ Erro ao salvar anotação")
            else:
                st.warning("Preencha símbolo e conteúdo")
    
    def render_saved_annotations(self, current_symbol=None):
        """Exibe anotações salvas"""
        annotations = self.get_user_annotations(current_symbol)
        
        if not annotations:
            st.sidebar.info("Nenhuma anotação salva")
            return
        
        # Filtro por categoria
        categories = list(set(anno['category'] for anno in annotations))
        selected_category = st.sidebar.selectbox(
            "Filtrar por categoria",
            options=["Todas"] + categories
        )
        
        # Aplica filtro
        filtered_annotations = [
            anno for anno in annotations 
            if selected_category == "Todas" or anno['category'] == selected_category
        ]
        
        for annotation in filtered_annotations[:10]:  # Limita a 10
            self.render_annotation_item(annotation)
    
    def render_annotation_item(self, annotation):
        """Renderiza um item de anotação individual"""
        with st.sidebar.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Ícone baseado na categoria
                category_icons = {
                    "compra": "🟢", "venda": "🔴", "alvo": "🎯",
                    "suporte": "📏", "resistência": "📊", "geral": "📝"
                }
                
                icon = category_icons.get(annotation['category'], "📝")
                st.write(f"{icon} **{annotation['symbol']}**")
                st.caption(annotation['content'][:50] + "..." if len(annotation['content']) > 50 else annotation['content'])
                st.caption(f"_{annotation['category']}_ • {self.format_date(annotation['created_at'])}")
            
            with col2:
                if st.button("🗑️", key=f"del_anno_{annotation['id']}"):
                    if self.delete_annotation(annotation['id']):
                        st.experimental_rerun()
            
            st.sidebar.markdown("---")
    
    def create_annotation(self, symbol, content, category, color, drawing_data):
        """Cria anotação no backend"""
        try:
            annotation_data = {
                "symbol": symbol.upper(),
                "content": content,
                "category": category,
                "color": color,
                "chart_time": datetime.now().timestamp(),
                "drawing_data": drawing_data
            }
            
            # Em produção, fazer requisição POST
            # response = requests.post(
            #     f"{API_BASE_URL}/api/annotations/{self.user_id}",
            #     json=annotation_data
            # )
            # return response.status_code == 200
            
            # Simulação para demo
            st.success(f"Anotação para {symbol} salva!")
            return True
            
        except Exception as e:
            st.error(f"Erro: {e}")
            return False
    
    def get_user_annotations(self, symbol=None):
        """Busca anotações do usuário"""
        try:
            # Em produção, fazer requisição GET
            # url = f"{API_BASE_URL}/api/annotations/{self.user_id}"
            # if symbol:
            #     url += f"?symbol={symbol}"
            # response = requests.get(url)
            # return response.json() if response.status_code == 200 else []
            
            # Dados de exemplo
            return [
                {
                    "id": "anno_1",
                    "symbol": "AAPL",
                    "content": "Rompeu resistência de $150, alvo $160",
                    "category": "alvo",
                    "color": "#00FF00",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "id": "anno_2",
                    "symbol": "TSLA",
                    "content": "Suporte em $200, stop em $195",
                    "category": "suporte", 
                    "color": "#FF6B6B",
                    "created_at": datetime.now().isoformat()
                }
            ]
        except:
            return []
    
    def delete_annotation(self, annotation_id):
        """Remove anotação"""
        try:
            # Em produção, fazer requisição DELETE
            # response = requests.delete(f"{API_BASE_URL}/api/annotations/{self.user_id}/{annotation_id}")
            # return response.status_code == 200
            
            # Simulação para demo
            st.success("Anotação removida!")
            return True
        except:
            st.error("Erro ao remover anotação")
            return False
    
    def format_date(self, date_string):
        """Formata data para exibição"""
        try:
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date.strftime("%d/%m %H:%M")
        except:
            return date_string

# Instância global
annotation_manager = AnnotationManager()