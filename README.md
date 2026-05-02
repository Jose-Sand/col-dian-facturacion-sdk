```markdown
# 📄 DIAN Facturación SDK

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DIAN](https://img.shields.io/badge/DIAN-Resolución%20000042-green.svg)](https://www.dian.gov.co)

SDK completo en Python para la generación, firma y transmisión de documentos de facturación electrónica conforme a la normativa de la DIAN (Dirección de Impuestos y Aduanas Nacionales) de Colombia.

## 🇨🇴 Contexto

Este SDK facilita la implementación de facturación electrónica en Colombia, cumpliendo con la **Resolución 000042 de 2020** y sus actualizaciones. Diseñado específicamente para el ecosistema colombiano y latinoamericano, simplifica el proceso técnico de generación de documentos UBL 2.1, firma digital y transmisión a proveedores tecnológicos homologados por la DIAN.

## ✨ Características

- ✅ **Generación UBL 2.1** conforme a estándar DIAN con validación XSD
- 🔐 **Firma XMLDSig** con certificado digital (.p12/.pfx) y timestamp
- 🔢 **Cálculo CUFE/CUDE** según algoritmo SHA-384 oficial
- 🚀 **Cliente HTTP** para envío a proveedores tecnológicos (CARVAJAL, DATAICO, EDICOM)
- 📋 **Plantillas** para factura electrónica, nota crédito, débito, documento equivalente POS
- 🛡️ **Validación exhaustiva** contra esquemas XSD oficiales de la DIAN
- 📦 **Soporte completo** para todos los documentos electrónicos requeridos

## 📦 Instalación

```bash
pip install dian-facturacion-sdk
```

### Instalación desde código fuente

```bash
git clone https://github.com/tu-usuario/dian-facturacion-sdk.git
cd dian-facturacion-sdk
pip install -e .
```

## 🚀 Uso Rápido

### 1. Generar Factura Electrónica UBL 2.1

```python
from dian_facturacion import UBLGenerator
from datetime import datetime

# Inicializar generador
generator = UBLGenerator()

# Datos de la factura
invoice_data = {
    "numero": "SETP990000001",
    "fecha_emision": datetime.now(),
    "fecha_vencimiento": datetime.now(),
    "emisor": {
        "nit": "900123456",
        "razon_social": "MI EMPRESA SAS",
        "nombre_comercial": "Mi Empresa",
        "direccion": "Calle 123 # 45-67",
        "ciudad": "Bogotá D.C.",
        "departamento": "Bogotá",
        "pais": "CO",
        "email": "facturacion@miempresa.co",
        "telefono": "+57 1 234 5678"
    },
    "receptor": {
        "tipo_documento": "31",  # NIT
        "numero_documento": "800234567",
        "razon_social": "CLIENTE EJEMPLO SAS",
        "email": "cliente@ejemplo.co",
        "direccion": "Carrera 98 # 76-54",
        "ciudad": "Medellín",
        "departamento": "Antioquia",
        "pais": "CO"
    },
    "items": [
        {
            "codigo": "PROD001",
            "descripcion": "Producto de ejemplo",
            "cantidad": 10,
            "unidad": "UND",
            "precio_unitario": 50000,
            "valor_total": 500000,
            "iva_porcentaje": 19,
            "iva_valor": 95000
        }
    ],
    "totales": {
        "subtotal": 500000,
        "iva": 95000,
        "total": 595000
    }
}

# Generar XML UBL
xml_invoice = generator.create_invoice(invoice_data)
print(xml_invoice)
```

### 2. Firmar Documento con Certificado Digital

```python
from dian_facturacion import DigitalSigner

# Inicializar firmador
signer = DigitalSigner(
    cert_path="certificado.p12",
    cert_password="mi_password_seguro"
)

# Firmar el XML
xml_signed = signer.sign_xml(
    xml_content=xml_invoice,
    signature_id="xmldsig-signature-001"
)

# Guardar XML firmado
with open("factura_firmada.xml", "w", encoding="utf-8") as f:
    f.write(xml_signed)
```

### 3. Calcular CUFE (Código Único de Factura Electrónica)

```python
from dian_facturacion import CUFECalculator

calculator = CUFECalculator()

cufe = calculator.calculate_cufe(
    numero_factura="SETP990000001",
    fecha_emision="20240115",
    hora_emision="10:30:00-05:00",
    valor_sin_iva="500000.00",
    codigo_impuesto_1="01",
    valor_impuesto_1="95000.00",
    codigo_impuesto_2="04",
    valor_impuesto_2="0.00",
    codigo_impuesto_3="03",
    valor_impuesto_3="0.00",
    valor_total="595000.00",
    nit_emisor="900123456",
    tipo_doc_receptor="31",
    numero_doc_receptor="800234567",
    software_pin="12345",
    tipo_ambiente="2"  # 1: Producción, 2: Habilitación
)

print(f"CUFE generado: {cufe}")
```

### 4. Enviar a Proveedor Tecnológico

```python
from dian_facturacion import ProviderClient

# Configurar cliente para proveedor
client = ProviderClient(
    provider="DATAICO",  # Opciones: CARVAJAL, DATAICO, EDICOM
    api_key="tu_api_key",
    environment="habilitacion"  # habilitacion o produccion
)

# Enviar documento
response = client.send_document(
    xml_content=xml_signed,
    document_type="invoice",
    attachments=["representacion_grafica.pdf"]
)

if response.success:
    print(f"✅ Documento enviado exitosamente")
    print(f"Tracking ID: {response.tracking