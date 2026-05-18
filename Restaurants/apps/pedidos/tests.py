from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from apps.pedidos.models import Ticket
from apps.pedidos.views import _promociones_elegibles
from apps.promociones.models import Promocion, Restricciones
from apps.usuarios.models import Cliente, Perfiles


class PromocionesPorVisitasTests(TestCase):
    def setUp(self):
        perfil = Perfiles.objects.create(tipo_de_usuario="Cliente")
        self.cliente = Cliente.objects.create(
            nombre_usuario="cliente5",
            numero_celular="3120000000",
            nombre="Cliente",
            apellido_paterno="Frecuente",
            contrase_a="demo",
            id_tipo_de_usuario=perfil,
        )
        self.restriccion = Restricciones.objects.create(
            nombre="5 visitas",
            consumo_minimo_para_aplicar=0,
            visitas_minimas_para_aplicar=5,
        )
        self.promocion = Promocion.objects.create(
            nombre="Cliente frecuente",
            descripcion="Descuento por visitas",
            porcentaje_a_reducir=Decimal("10.00"),
            id_restriccion=self.restriccion,
        )

    def _crear_ticket(self, codigo):
        return Ticket.objects.create(
            precio_final=Decimal("100.00"),
            fecha=timezone.now(),
            canjeado=1,
            nombre_usuario=self.cliente,
            codigounico=codigo,
            metodo_pago="efectivo",
            pagado=True,
        )

    def test_promocion_no_es_elegible_con_menos_visitas(self):
        for codigo in range(100001, 100005):
            self._crear_ticket(codigo)

        elegibles = _promociones_elegibles(self.cliente, total_productos=1)

        self.assertNotIn(self.promocion, elegibles)

    def test_promocion_es_elegible_con_visitas_minimas(self):
        for codigo in range(100001, 100006):
            self._crear_ticket(codigo)

        elegibles = _promociones_elegibles(self.cliente, total_productos=1)

        self.assertIn(self.promocion, elegibles)
