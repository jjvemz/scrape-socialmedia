#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.scrapfly_config import ScrapFlyConfig

def debug_instagram_config():
    print("🔍 DIAGNÓSTICO DE CONFIGURACIÓN INSTAGRAM")
    print("="*50)
    
    try:
        config = ScrapFlyConfig()
        
        # 1. Verificar configuración de plataforma
        print("\n1️⃣ Verificando platform_configs...")
        instagram_config = config.platform_configs.get('instagram', {})
        print(f"   • ASP en platform_config: {instagram_config.get('asp', 'NO ENCONTRADO')}")
        print(f"   • Budget en platform_config: {instagram_config.get('cost_budget', 'NO ENCONTRADO')}")
        print(f"   • Timeout en platform_config: {instagram_config.get('timeout', 'NO ENCONTRADO')}")
        
        headers = instagram_config.get('additional_headers', {})
        print(f"   • Header x-ig-app-id: {headers.get('x-ig-app-id', 'NO ENCONTRADO')}")
        
        # 2. Verificar creación de configuración
        print("\n2️⃣ Verificando create_scrape_config...")
        test_config = config.create_scrape_config("https://www.instagram.com/test", 'instagram')
        
        print(f"   • ASP en ScrapeConfig: {getattr(test_config, 'asp', 'NO ENCONTRADO')}")
        print(f"   • Budget en ScrapeConfig: {getattr(test_config, 'cost_budget', 'NO ENCONTRADO')}")
        print(f"   • Timeout en ScrapeConfig: {getattr(test_config, 'timeout', 'NO ENCONTRADO')}")
        print(f"   • Proxy en ScrapeConfig: {getattr(test_config, 'proxy_pool', 'NO ENCONTRADO')}")
        
        config_headers = getattr(test_config, 'headers', {})
        print(f"   • Header x-ig-app-id en config: {config_headers.get('x-ig-app-id', 'NO ENCONTRADO')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_instagram_config()
    input("\nPresiona Enter para salir...")