"""
Tests unitarios para generación UBL, firma digital, cálculo CUFE y envío a proveedores tecnológicos

Este módulo contiene tests exhaustivos para verificar:
- Generación correcta de documentos UBL 2.1 según estándar DIAN
- Firma XMLDSig con certificados digitales colombianos
- Cálculo preciso de CUFE/CUDE con algoritmo SHA-384
- Validación contra esquemas XSD oficiales
- Integración con proveedores tecnológicos homologados
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from pathlib import Path
from lxml import etree
from cryptography import x509
from cryptography.hazmat.backends import default_backend
import hashlib
import base64

from dian_facturacion.ubl_generator import (
    UBLGenerator,
    InvoiceData,
    Party,
    TaxTotal,
    InvoiceLine,
    DocumentType
)
from dian_facturacion.digital_signer import (
    DigitalSigner,
    SignatureConfig,
    CertificateInfo
)


@pytest.fixture
def emisor_prueba():
    """Fixture con datos de emisor de prueba según ambiente habilitación DIAN"""
    return Party(
        identification_number="900123456",
        identification_type="31",  # NIT
        check_digit="7",
        legal_name="EMPRESA DE PRUEBAS FACTURACION SAS",
        trade_name="PRUEBAS FACT",
        tax_level_code="O-13",  # Responsable de IVA
        address={
            "department": "11",  # Bogotá D.C.
            "city": "11001",  # Bogotá
            "address_line": "Carrera 7 No 32-16",
            "postal_zone": "110231"
        },
        phone="6012345678",
        email="facturacion@pruebas.com.co",
        tax_scheme="01",  # IVA
        fiscal_responsibilities=["R-99-PN"]
    )


@pytest.fixture
def adquiriente_prueba():
    """Fixture con datos de adquiriente de prueba"""
    return Party(
        identification_number="79123456",
        identification_type="13",  # Cédula de ciudadanía
        check_digit=None,
        legal_name="JUAN CARLOS PÉREZ GÓMEZ",
        trade_name=None,
        tax_level_code="R-99-PN",  # No responsable de IVA
        address={
            "department": "76",  # Valle del Cauca
            "city": "76001",  # Cali
            "address_line": "Avenida 5N No 24-33",
            "postal_zone": "760001"
        },
        phone="6025551234",
        email="juan.perez@email.com",
        tax_scheme="ZZ",  # No aplica
        fiscal_responsibilities=["R-99-PN"]
    )


@pytest.fixture
def lineas_factura_prueba():
    """Fixture con líneas de factura de ejemplo"""
    return [
        InvoiceLine(
            line_number=1,
            quantity=Decimal("2.00"),
            unit_code="94",  # Unidad (UBL)
            description="Computador portátil DELL Inspiron 15",
            item_code="COMP-DELL-001",
            unit_price=Decimal("1800000.00"),
            tax_category="01",  # IVA
            tax_rate=Decimal("19.00"),
            line_extension_amount=Decimal("3600000.00")
        ),
        InvoiceLine(
            line_number=2,
            quantity=Decimal("1.00"),
            unit_code="94",
            description="Mouse inalámbrico Logitech M170",
            item_code="MOUSE-LOG-170",
            unit_price=Decimal("45000.00"),
            tax_category="01",
            tax_rate=Decimal("19.00"),
            line_extension_amount=Decimal("45000.00")
        )
    ]


@pytest.fixture
def impuestos_factura_prueba():
    """Fixture con totales de impuestos calculados"""
    return [
        TaxTotal(
            tax_id="01",  # IVA
            tax_name="IVA",
            taxable_amount=Decimal("3645000.00"),
            tax_amount=Decimal("692550.00"),
            tax_percentage=Decimal("19.00")
        )
    ]


@pytest.fixture
def datos_factura_completa(emisor_prueba, adquiriente_prueba, lineas_factura_prueba, impuestos_factura_prueba):
    """Fixture con datos completos de factura electrónica"""
    return InvoiceData(
        document_type=DocumentType.FACTURA_VENTA,
        invoice_number="SETT990000001",
        invoice_date=date(2024, 1, 15),
        invoice_time=datetime(2024, 1, 15, 10, 30, 0),
        currency_code="COP",
        supplier=emisor_prueba,
        customer=adquiriente_prueba,
        invoice_lines=lineas_factura_prueba,
        tax_totals=impuestos_factura_prueba,
        legal_monetary_total={
            "line_extension_amount": Decimal("3645000.00"),
            "tax_exclusive_amount": Decimal("3645000.00"),
            "tax_inclusive_amount": Decimal("4337550.00"),
            "payable_amount": Decimal("4337550.00")
        },
        payment_means_code="10",  # Efectivo
        payment_due_date=date(2024, 1, 22),
        notes=["Factura de prueba para homologación DIAN"],
        order_reference=None
    )


@pytest.fixture
def certificado_prueba(tmp_path):
    """
    Fixture que proporciona ruta a certificado de prueba.
    En ambiente real, usar certificado emitido por entidad certificadora autorizada.
    """
    cert_path = tmp_path / "certificado_prueba.p12"
    # En producción, aquí iría un certificado real de prueba provisto por la DIAN
    # Para tests, se simula la existencia del archivo
    cert_path.write_bytes(b"MOCK_CERTIFICATE_DATA")
    return str(cert_path)


@pytest.fixture
def ubl_generator():
    """Fixture con instancia de generador UBL"""
    return UBLGenerator(
        validate_xsd=False,  # Deshabilitado para tests unitarios rápidos
        environment="habilitacion"  # Ambiente de pruebas DIAN
    )


@pytest.fixture
def digital_signer():
    """Fixture con instancia de firmador digital (mock)"""
    return Dig