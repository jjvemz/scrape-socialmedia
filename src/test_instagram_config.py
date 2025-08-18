#!/usr/bin/env python3
"""
Test rápido para verificar configuración de Instagram con ScrapFly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.scrapfly_config import ScrapFlyConfig
from utils.scrapfly_validator import ScrapFlyValidator

def test_instagram_configuration():
    """Test rápido de configuración Instagram"""
    print("🧪 TEST RÁPIDO - CONFIGURACIÓN INSTAGRAM")
    print("="*50)
    
    try:
        # 1. Validar configuración
        print("\n1️⃣ Ejecutando validación...")
        validator = ScrapFlyValidator()
        validation_ok = validator.run_full_validation()
        
        if not validation_ok:
            print("❌ Validación falló. Revisa los errores arriba.")
            return False
        
        # 2. Test de configuración específica
        print("\n2️⃣ Probando configuración Instagram...")
        config = ScrapFlyConfig()
        
        # Crear configuración de prueba
        test_config = config.create_scrape_config(
            "https://www.instagram.com/test", 
            'instagram'
        )
        
        print(f"✅ Config generada:")
        print(f"   • ASP: {getattr(test_config, 'asp', False)}")
        print(f"   • Budget: {getattr(test_config, 'cost_budget', 0)}")
        print(f"   • Proxy: {getattr(test_config, 'proxy_pool', 'N/A')}")
        print(f"   • Timeout: {getattr(test_config, 'timeout', 0)/1000}s")
        print(f"   • Session: {getattr(test_config, 'session', 'N/A')[:30]}...")
        
        # 3. Verificar headers críticos
        headers = getattr(test_config, 'headers', {})
        x_ig_app_id = headers.get('x-ig-app-id', '')
        
        if x_ig_app_id == '936619743392459':
            print(f"✅ Header x-ig-app-id: Correcto")
        else:
            print(f"❌ Header x-ig-app-id: {x_ig_app_id}")
            return False
        
        print("\n✅ Configuración Instagram lista para usar!")
        return True
        
    except Exception as e:
        print(f"❌ Error en test: {str(e)}")
        return False

def main():
    success = test_instagram_configuration()
    
    if success:
        print("\n🎉 ¡Todo configurado correctamente!")
        print("   Puedes ejecutar el scraper con confianza.")
    else:
        print("\n⚠️ Hay problemas de configuración.")
        print("   Revisa los errores antes de hacer scraping.")
    
    input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    main()