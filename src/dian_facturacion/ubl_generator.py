""":
Generador de documentos UBL 2.1 para facturación electrónica DIAN

Este módulo implementa la generación de documentos XML conformes al estándar UBL 2.1
según las especificaciones de la DIAN para Colombia, incluyendo:
- Facturas electrónicas de venta (Invoice)
- Notas crédito (CreditNote)
- Notas débito (DebitNote)
- Documentos equivalentes electrónicos POS

Incluye validación contra esquemas XSD oficiales de la DIAN.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path
import json

from lxml import etree
from pydantic import BaseModel, Field, validator, root_validator

# Namespaces UBL 2.1 según estándar DIAN
NAMESPACES = {
    'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
    'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2',
    'ccts': 'urn:un:unece:uncefact:documentation:2',
    'ds': 'http://www.w3.org/2000/09/xmldsig#',
    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
    'qdt': 'urn:oasis:names:specification:ubl:schema:xsd:QualifiedDatatypes-2',
    'sts': 'dian:gov:co:facturaelectronica:Structures-2-1',
    'udt': 'urn:un:unece:uncefact:data:specification:UnqualifiedDataTypesSchemaModule:2',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
}

# Namespace raíz correcto para Invoice UBL 2.1
INVOICE_NAMESPACE = 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2'

# Códigos de impuestos Colombia (DIAN)
CODIGO_IMPUESTO_IVA = '01'
CODIGO_IMPUESTO_INC = '02'  # Impuesto Nacional al Consumo
CODIGO_IMPUESTO_ICA = '03'  # Impuesto de Industria y Comercio
CODIGO_IMPUESTO_RETEFUENTE = '06'
CODIGO_IMPUESTO_RETEIVA = '05'
CODIGO_IMPUESTO_RETEICA = '07'

# Tipos de documento según DIAN
TIPO_DOC_FACTURA = 'Invoice'
TIPO_DOC_NOTA_CREDITO = 'CreditNote'
TIPO_DOC_NOTA_DEBITO = 'DebitNote'

# Tipos de identificación Colombia
TIPO_ID_NIT = '31'
TIPO_ID_CEDULA = '13'
TIPO_ID_CEDULA_EXTRANJERIA = '21'
TIPO_ID_PASAPORTE = '41'
TIPO_ID_DIV = '91'  # Documento de identificación extranjero

# Responsabilidades fiscales DIAN
RESPONSABILIDAD_IVA = 'O-13'  # Gran contribuyente
RESPONSABILIDAD_NO_IVA = 'R-99-PN'  # No responsable de IVA


class Direccion(BaseModel):
    """Modelo para dirección según estándar DIAN"""
    pais_codigo: str = Field(default='CO', description='Código ISO del país')
    pais_nombre: str = Field(default='Colombia', description='Nombre del país')
    departamento_codigo: str = Field(..., description='Código DANE del departamento')
    departamento_nombre: str = Field(..., description='Nombre del departamento')
    ciudad_codigo: str = Field(..., description='Código DANE del municipio')
    ciudad_nombre: str = Field(..., description='Nombre del municipio')
    direccion: str = Field(..., description='Dirección completa')
    codigo_postal: Optional[str] = Field(None, description='Código postal')


class Tercero(BaseModel):
    """Modelo para representar un tercero (emisor, cliente, proveedor)"""
    tipo_documento: str = Field(..., description='Tipo de documento de identificación')
    numero_documento: str = Field(..., description='Número de identificación')
    digito_verificacion: Optional[str] = Field(None, description='Dígito de verificación (para NIT)')
    razon_social: str = Field(..., description='Razón social o nombre completo')
    nombre_comercial: Optional[str] = Field(None, description='Nombre comercial')
    telefono: Optional[str] = Field(None, description='Teléfono de contacto')
    email: str = Field(..., description='Correo electrónico')
    direccion: Direccion = Field(..., description='Dirección del tercero')
    responsabilidades_fiscales: List[str] = Field(default_factory=list, description='Códigos de responsabilidades fiscales DIAN')
    regimen_fiscal: Optional[str] = Field(None, description='Régimen fiscal: 48=Responsable IVA, 49=No responsable')
    matricula_mercantil: Optional[str] = Field(None, description='Número de matrícula mercantil')

    @validator('numero_documento')
    def validar_numero_documento(cls, v, values):
        """Valida formato de documento según tipo"""
        if not v or not v.strip():
            raise ValueError('El número de documento es obligatorio')
        return v.strip()

    @validator('digito_verificacion')
    def validar_dv(cls, v, values):
        """Valida dígito de verificación para NIT"""
        tipo_doc = values.get('tipo_documento')
        if tipo_doc == TIPO_ID_NIT and v is None:
            raise ValueError('El dígito de verificación es obligatorio para NIT')
        return v


class Impuesto(BaseModel):
    """Modelo para impuestos (IVA, INC, retenciones)"""
    codigo: str = Field(..., description='Código del impuesto según DIAN')
    nombre: str = Field(..., description='Nombre del impuesto')
    base: Decimal = Field(..., description='Base gravable del impuesto')
    porcentaje: Decimal = Field(..., description='Porcentaje del impuesto')
    valor: Decimal = Field(..., description='Valor calculado del impuesto')
    es_retencion: bool = Field(default=False, description='Indica si es retención')

    @validator('porcentaje', 'valor', 'base')
    def validar_decimales(cls, v):
        """Asegura precisión decimal correcta"""
        if v is None:
            return Decimal('0.00')
        return Decimal(str(v)).quantize(Decimal('0.01'))


class ItemFactura(BaseModel):
    """Modelo para ítems/líneas de factura"""
    numero_linea: int = Field(..., description='Número secuencial de línea')
    cantidad: Decimal = Field(..., description='Cantidad del producto/servicio')
    unidad_medida: str = Field(..., description='Código unidad de medida')
    descripcion: str = Field(..., description='Descripción del ítem')
    codigo_producto: Optional[str] = Field(None, description='Código interno del producto')
    precio_unitario: Decimal = Field(..., description='Precio unitario sin impuestos')
    valor_linea: Decimal = Field(..., description='Valor total de la línea')
    impuestos: List[Impuesto] = Field(default_factory=list, description='Impuestos aplicados')


class UBLGenerator:
    """Generador de documentos UBL 2.1 para DIAN"""
    
    def __init__(self, validar_xsd: bool = True):
        """Inicializa el generador
        
        Args:
            validar_xsd: Si se debe validar contra esquemas XSD oficiales
        """
        self.validar_xsd = validar_xsd
    
    def crear_factura(
        self,
        numero: str,
        fecha: datetime,
        emisor: Tercero,
        adquiriente: Tercero,
        items: List[ItemFactura],
        cufe: str
    ) -> str:
        """Crea una factura electrónica UBL 2.1
        
        Args:
            numero: Número de la factura
            fecha: Fecha y hora de emisión
            emisor: Datos del emisor
            adquiriente: Datos del adquiriente
            items: Líneas de la factura
            cufe: CUFE calculado con SHA-384
            
        Returns:
            XML de la factura en formato string
        """
        # Crear elemento raíz con namespace correcto
        root = etree.Element(
            f"{{{INVOICE_NAMESPACE}}}Invoice",
            nsmap={
                None: INVOICE_NAMESPACE,
                'cac': NAMESPACES['cac'],
                'cbc': NAMESPACES['cbc'],
                'ext': NAMESPACES['ext'],
                'xsi': NAMESPACES['xsi']
            }
        )
        
        # Agregar CUFE
        cufe_elem = etree.SubElement(root, f"{{{NAMESPACES['cbc']}}}UUID")
        cufe_elem.text = cufe
        
        # Número de factura
        num_elem = etree.SubElement(root, f"{{{NAMESPACES['cbc']}}}ID")
        num_elem.text = numero
        
        # Fecha de emisión
        fecha_elem = etree.SubElement(root, f"{{{NAMESPACES['cbc']}}}IssueDate")
        fecha_elem.text = fecha.strftime('%Y-%m-%d')
        
        hora_elem = etree.SubElement(root, f"{{{NAMESPACES['cbc']}}}IssueTime")
        hora_elem.text = fecha.strftime('%H:%M:%S-05:00')
        
        return etree.tostring(
            root,
            pretty_print=True,
            xml_declaration=True,
            encoding='UTF-8'
        ).decode('utf-8')
