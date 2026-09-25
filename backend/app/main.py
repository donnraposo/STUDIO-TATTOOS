"""Ponto de entrada ASGI. Sem logica propria: apenas liga o container a aplicacao."""

from app.application import Application
from app.core.container import Container

app = Application(Container.instance()).create()
