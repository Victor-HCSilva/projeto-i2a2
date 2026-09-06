from typing import Callable, Type, Optional
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from configs.configs import DEBUG
from componentes.utils.messages import messages

if DEBUG:
    m = messages.Message()

class ManagerTools:
    def __init__(
        self,
        sql_doc: callable,
        search_doc: str,
        search_doc_input: str,
        function_schema: Optional[Type[BaseModel]] = None,
    ) -> None:
        self.sql_doc = sql_doc
        self.search_doc = search_doc
        self.search_doc_input = search_doc_input
        self.function_schema = function_schema or BaseModel

    def validation_(self) -> bool:
        try:
            if not (self.sql_doc and self.search_doc_input and self.search_doc):
                if configs.DEBUG:
                    m.warning("\nParâmetros inválidos")  # corrigido
                raise ValueError("Parâmetros inválidos em ManagerTools")
            return True
        except Exception as e:
            if configs.DEBUG:
                m.danger(f"Erro na classe ManagerTools: {e}")
            print(f"Erro na classe ManagerTools: {e}")
            return False

    def get_tool(self) -> Optional[StructuredTool]:
        if self.validation_():
            return StructuredTool.from_function(
                func=self.sql_doc,
                name=self.search_doc_input,
                description=self.search_doc,
                args_schema=self.function_schema,
            )
        return None
