from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class OutlierInput(BaseModel):
    coluna: str = Field(..., description="Coluna numérica para detectar outliers")


class GraphInput(BaseModel):
    tipo: str = Field(
        ...,
        description="Tipo de gráfico: barras, linha, pontos, caixa, pizza, histograma, calor",
    )
    x: Optional[str] = Field(None, description="Coluna X ou categoria")
    y: Optional[str] = Field(None, description="Coluna Y ou valores")


class ScatterInput(BaseModel):
    x: str = Field(..., description="Coluna para o eixo X")
    y: str = Field(..., description="Coluna para o eixo Y")
    title: Optional[str] = Field(None, description="Título opcional do gráfico")


class SearchDocumentInput(BaseModel):
    query: str = Field(..., description="Consulta para busca semântica")


class SQLDocumentInput(BaseModel):
    query: str = Field(..., description="Consulta em SQL sobre o conjunto de dados")


def _graph_tool_impl(args: GraphInput) -> str:
    return (
        f"Gráfico do tipo {args.tipo} solicitado para x={args.x} e y={args.y}. "
        "Este utilitário de schema é usado pelo pipeline de configuração do agente."
    )


def _scatter_tool_impl(args: ScatterInput) -> str:
    return (
        f"Gráfico de dispersão solicitado para x={args.x} e y={args.y}. "
        f"Título: {args.title or 'sem título'}."
    )


graph_tool = StructuredTool.from_function(
    func=_graph_tool_impl,
    name="gerar_grafico",
    description="Gera gráficos a partir do CSV",
    args_schema=GraphInput,
)

scatter_tool = StructuredTool.from_function(
    func=_scatter_tool_impl,
    name="gerar_grafico_dispersao",
    description="Gera gráfico de dispersão a partir dos dados",
    args_schema=ScatterInput,
)

__all__ = [
    "OutlierInput",
    "GraphInput",
    "ScatterInput",
    "SearchDocumentInput",
    "SQLDocumentInput",
    "graph_tool",
    "scatter_tool",
]
