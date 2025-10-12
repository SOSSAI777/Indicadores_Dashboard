import streamlit as st
import plotly.graph_objects as go
from typing import Dict, List, Optional

class DrawingTools:
    def __init__(self):
        self.tools = {
            "horizontal_line": {"name": "Linha Horizontal", "icon": "➖"},
            "vertical_line": {"name": "Linha Vertical", "icon": "📏"},
            "trend_line": {"name": "Linha de Tendência", "icon": "📈"},
            "fibonacci_retracement": {"name": "Fibonacci", "icon": "📊"},
            "rectangle": {"name": "Retângulo", "icon": "⬜"},
            "text": {"name": "Texto", "icon": "🔤"}
        }
        self.active_tool = None
        self.drawings = []
    
    def render_controls(self):
        """Renderiza controles de desenho na sidebar"""
        st.sidebar.markdown("---")
        st.sidebar.subheader("🛠️ Ferramentas de Desenho")
        
        # Seleção de ferramenta
        tool_options = [f"{tool['icon']} {name}" for name, tool in self.tools.items()]
        selected_tool_display = st.sidebar.selectbox(
            "Ferramenta:",
            options=tool_options,
            index=0
        )
        
        # Extrai o nome da ferramenta da string de display
        self.active_tool = selected_tool_display.split(" ")[1]
        
        # Configurações específicas por ferramenta
        if self.active_tool == "horizontal_line":
            st.sidebar.color_picker("Cor", value="#FF0000")
            st.sidebar.selectbox("Estilo", ["Solid", "Dashed", "Dotted"])
            
        elif self.active_tool == "trend_line":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.color_picker("Cor", value="#2962FF")
            with col2:
                st.number_input("Espessura", min_value=1, max_value=5, value=2)
                
        elif self.active_tool == "fibonacci_retracement":
            st.sidebar.checkbox("Mostrar níveis", value=True)
            st.sidebar.checkbox("Mostrar preços", value=True)
            
        elif self.active_tool == "text":
            st.sidebar.text_input("Texto", value="Anotação")
            st.sidebar.color_picker("Cor do texto", value="#FFFFFF")
        
        # Botão de limpar desenhos
        if st.sidebar.button("🗑️ Limpar Todos os Desenhos"):
            self.drawings.clear()
            st.experimental_rerun()
        
        return self.active_tool
    
    def add_drawing(self, drawing_data: Dict):
        """Adiciona um desenho à lista"""
        drawing_data['id'] = f"drawing_{len(self.drawings) + 1}"
        self.drawings.append(drawing_data)
    
    def apply_drawings_to_chart(self, fig: go.Figure) -> go.Figure:
        """Aplica os desenhos ao gráfico Plotly"""
        for drawing in self.drawings:
            fig = self._add_drawing_to_figure(fig, drawing)
        return fig
    
    def _add_drawing_to_figure(self, fig: go.Figure, drawing: Dict) -> go.Figure:
        """Adiciona um desenho específico à figura"""
        drawing_type = drawing.get('type')
        
        if drawing_type == 'horizontal_line':
            fig.add_hline(
                y=drawing['y'],
                line_dash=drawing.get('style', 'solid'),
                line_color=drawing.get('color', '#FF0000'),
                line_width=drawing.get('width', 1),
                annotation_text=drawing.get('label', '')
            )
            
        elif drawing_type == 'vertical_line':
            fig.add_vline(
                x=drawing['x'],
                line_dash=drawing.get('style', 'solid'),
                line_color=drawing.get('color', '#FF0000'),
                line_width=drawing.get('width', 1)
            )
            
        elif drawing_type == 'trend_line':
            fig.add_trace(
                go.Scatter(
                    x=[drawing['x0'], drawing['x1']],
                    y=[drawing['y0'], drawing['y1']],
                    mode='lines',
                    line=dict(
                        color=drawing.get('color', '#2962FF'),
                        width=drawing.get('width', 2),
                        dash=drawing.get('style', 'solid')
                    ),
                    showlegend=False
                )
            )
            
        elif drawing_type == 'fibonacci_retracement':
            # Implementação simplificada do Fibonacci
            high = drawing['high']
            low = drawing['low']
            levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1]
            
            for level in levels:
                price = high - (high - low) * level
                fig.add_hline(
                    y=price,
                    line_dash='dash',
                    line_color='#FFA000',
                    annotation_text=f"FIB {level*100}%"
                )
                
        elif drawing_type == 'rectangle':
            fig.add_shape(
                type="rect",
                x0=drawing['x0'], y0=drawing['y0'],
                x1=drawing['x1'], y1=drawing['y1'],
                line=dict(
                    color=drawing.get('color', '#00FF00'),
                    width=drawing.get('width', 1),
                ),
                fillcolor=drawing.get('fillcolor', 'rgba(0,255,0,0.1)'),
            )
            
        elif drawing_type == 'text':
            fig.add_annotation(
                x=drawing['x'],
                y=drawing['y'],
                text=drawing['text'],
                showarrow=True,
                arrowhead=2,
                bgcolor=drawing.get('bgcolor', 'rgba(0,0,0,0.8)'),
                bordercolor=drawing.get('bordercolor', '#FFFFFF'),
                font=dict(color=drawing.get('color', '#FFFFFF'))
            )
        
        return fig

# Instância global
drawing_tools = DrawingTools()