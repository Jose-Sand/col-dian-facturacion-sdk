""":
SDK para Facturación Electrónica Colombia (DIAN)

Este paquete proporciona herramientas completas para generar, firmar y transmitir
documentos de facturación electrónica conforme a los estándares de la DIAN:

- Generación de documentos UBL 2.1 (facturas, notas crédito/débito, documentos equivalentes)
- Firma digital XMLDSig con certificados .p12/.pfx
- Cálculo de CUFE/CUDE según algoritmo SHA-384 oficial
- Validación contra esquemas XSD de la DIAN
- Integración con proveedores tecnológicos homologados

Ejemplo de uso básico:
    >>> from dian_facturacion import UBLGenerator, XMLSigner, CUFECalculator
    >>> 
    >>> # Generar factura UBL 2.1
    >>> generator = UBLGenerator()
    >>> factura_xml = generator.crear_factura(
    ...     emisor=emisor_data,
    ...     adquiriente=adquiriente_data,
    ...     items=items_data
    ... )
    >>> 
    >>> # Calcular CUFE
    >>> cufe_calc = CUFECalculator()
    >>> cufe = cufe_calc.calcular_cufe(factura_xml)
    >>> 
    >>> # Firmar documento
    >>> signer = XMLSigner(cert_path="certificado.p12", password="secreto")
    >>> xml_firmado = signer.firmar(factura_xml)
    >>> 
    >>> # Enviar a proveedor tecnológico
    >>> from dian_facturacion import ProveedorClient
    >>> client = ProveedorClient(proveedor="CARVAJAL", credentials=creds)
    >>> response = client.enviar_factura(xml_firmado)

Componentes principales:
    - UBLGenerator: Generación de documentos UBL 2.1
    - XMLSigner: Firma digital con certificados digitales
    - CUFECalculator: Cálculo de códigos únicos (CUFE/CUDE/CUDS)
    - XSDValidator: Validación contra esquemas DIAN
    - ProveedorClient: Cliente HTTP para proveedores tecnológicos
    - DocumentTypes: Enumeraciones de tipos de documentos
    - TipoDocumento: Constantes de identificación tributaria

Licencia: MIT
Autor: DIAN Facturación SDK Contributors
Versión: 1.0.0
"""

from dian_facturacion.core.ubl_generator import UBLGenerator
from dian_facturacion.core.xml_signer import XMLSigner
from dian_facturacion.core.cufe_calculator import CUFECalculator
from dian_facturacion.core.xsd_validator import XSDValidator
from dian_facturacion.client.proveedor_client import ProveedorClient
from dian_facturacion.models.tipos import (
    TipoDocumento,
    TipoOperacion,
    TipoContribuyente,
    ResponsabilidadFiscal,
    TipoPersona,
    RegimenFiscal,
)
from dian_facturacion.models.factura import (
    Emisor,
    Adquiriente,
    Item,
    Impuesto,
    Factura,
    MedioPago,
)
from dian_facturacion.models.nota_credito import NotaCredito, MotivoNotaCredito
from dian_facturacion.models.nota_debito import NotaDebito, MotivoNotaDebito
from dian_facturacion.models.documento_equivalente import (
    DocumentoEquivalente,
    TipoDocumentoEquivalente,
)
from dian_facturacion.utils.validaciones import (
    validar_nit,
    validar_cedula,
    validar_fecha,
    validar_monto,
)
from dian_facturacion.utils.formateo import (
    formatear_nit,
    formatear_moneda,
    formatear_fecha_dian,
)
from dian_facturacion.exceptions import (
    DIANException,
    UBLGenerationError,
    SignatureError,
    CUFECalculationError,
    ValidationError,
    ProveedorError,
)

__version__ = "1.0.0"
__author__ = "DIAN Facturación SDK Contributors"
__license__ = "MIT"

__all__ = [
    # Versión
    "__version__",
    "__author__",
    "__license__",
    
    # Core - Componentes principales
    "UBLGenerator",
    "XMLSigner",
    "CUFECalculator",
    "XSDValidator",
    
    # Cliente de proveedores
    "ProveedorClient",
    
    # Modelos - Entidades principales
    "Emisor",
    "Adquiriente",
    "Item",
    "Impuesto",
    "Factura",
    "MedioPago",
    "NotaCredito",
    "MotivoNotaCredito",
    "NotaDebito",
    "MotivoNotaDebito",
    "DocumentoEquivalente",
    "TipoDocumentoEquivalente",
    
    # Tipos y enumeraciones
    "TipoDocumento",
    "TipoOperacion",
    "TipoContribuyente",
    "ResponsabilidadFiscal",
    "TipoPersona",
    "RegimenFiscal",
    
    # Utilidades de validación
    "validar_nit",
    "validar_cedula",
    "validar_fecha",
    "validar_monto",
    
    # Utilidades de formateo
    "formatear_nit",
    "formatear_moneda",
    "formatear_fecha_dian",
    
    # Excepciones
    "DIANException",
    "UBLGenerationError",
    "SignatureError",
    "CUFECalculationError",
    "ValidationError",
    "ProveedorError",
]


def configurar_sdk(
    ambiente: str = "habilitacion",
    timeout: int = 30,
    reintentos: int = 3,
    verificar_ssl: bool = True,
    log_level: str = "INFO"
) -> None:
    """
    Configura parámetros globales del SDK.
    
    Establece configuración general para todos los componentes del SDK,
    incluyendo ambiente de ejecución (habilitación/producción), timeouts
    de conexión, política de reintentos y nivel de logging.
    
    Args:
        ambiente: Ambiente de operación, 'habilitacion' o 'produccion'
        timeout: Timeout en segundos para peticiones HTTP (default: 30)
        reintentos: Número máximo de reintentos en caso de error (default: 3)
        verificar_ssl: Si se debe verificar certificados SSL (default: True)
        log_level: Nivel de logging ('DEBUG', 'INFO', 'WARNING', 'ERROR')
    """
    import logging
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configurar variables globales del SDK
    from dian_facturacion import config
    config.AMBIENTE = ambiente
    config.TIMEOUT = timeout
    config.REINTENTOS = reintentos
    config.VERIFICAR_SSL = verificar_ssl
