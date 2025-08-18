#!/usr/bin/env python3
"""
Validador de configuración ScrapFly para Instagram Scraping
Verifica que todos los criterios críticos estén configurados correctamente
"""

import sys
import os
from colorama import Fore, Style, init

# Añadir el directorio actual al path para imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from scrapfly_config import ScrapFlyConfig

# Inicializar colorama
init(autoreset=True)

class ScrapFlyValidator:
    def __init__(self):
        self.scrapfly_config = None
        self.validation_results = []
        
    def run_full_validation(self):
        """Ejecuta validación completa según checklist ScrapFly 2025"""
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}    VALIDADOR SCRAPFLY - INSTAGRAM SCRAPING 2025")
        print(f"{Fore.CYAN}{'='*70}")
        print()
        
        try:
            # ✅ Paso 1: Verificar API Key y Créditos
            self._validate_api_key_and_credits()
            
            # ✅ Paso 2: Verificar configuración ASP
            self._validate_asp_configuration()
            
            # ✅ Paso 3: Verificar proxies residenciales
            self._validate_proxy_configuration()
            
            # ✅ Paso 4: Verificar headers críticos
            self._validate_instagram_headers()
            
            # ✅ Paso 5: Verificar timeouts
            self._validate_timeout_configuration()
            
            # ✅ Paso 6: Verificar manejo de sesiones
            self._validate_session_management()
            
            # ✅ Paso 7: Verificar retry logic
            self._validate_retry_logic()
            
            # ✅ Mostrar resultados finales
            self._show_validation_summary()
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error crítico en validación: {str(e)}")
            return False
    
    def _validate_api_key_and_credits(self):
        """✅ Paso 1: Verificar API Key y Créditos"""
        print(f"{Fore.YELLOW}🔍 PASO 1: Verificando API Key y Créditos...")
        
        try:
            self.scrapfly_config = ScrapFlyConfig()
            
            if not self.scrapfly_config.client:
                self._add_result("❌", "API Key", "Cliente ScrapFly no inicializado - verifica tu API key")
                return
            
            # Verificar conexión
            connection_ok = self.scrapfly_config.verify_connection()
            
            if connection_ok:
                self._add_result("✅", "API Key", "Válida y funcionando")
                self._add_result("✅", "Conexión", "ScrapFly conectado exitosamente")
            else:
                self._add_result("❌", "API Key", "Conexión fallida - verifica API key y créditos")
                
        except Exception as e:
            self._add_result("❌", "API Key", f"Error: {str(e)}")
    
    def _validate_asp_configuration(self):
        """✅ Paso 2: Verificar configuración ASP"""
        print(f"{Fore.YELLOW}🛡️ PASO 2: Verificando Anti-Scraping Protection...")
        
        try:
            instagram_config = self.scrapfly_config.platform_configs.get('instagram', {})
            
            # Verificar que ASP esté habilitado
            asp_enabled = instagram_config.get('asp', False)
            if asp_enabled:
                self._add_result("✅", "ASP", "Habilitado correctamente")
            else:
                self._add_result("❌", "ASP", "NO habilitado - CRÍTICO para Instagram")
            
            # Verificar presupuesto
            cost_budget = instagram_config.get('cost_budget', 0)
            if cost_budget >= 55:
                self._add_result("✅", "Budget ASP", f"{cost_budget} créditos (adecuado)")
            elif cost_budget >= 25:
                self._add_result("⚠️", "Budget ASP", f"{cost_budget} créditos (mínimo)")
            else:
                self._add_result("❌", "Budget ASP", f"{cost_budget} créditos (insuficiente)")
                
        except Exception as e:
            self._add_result("❌", "ASP Config", f"Error: {str(e)}")
    
    def _validate_proxy_configuration(self):
        """✅ Paso 3: Verificar proxies residenciales"""
        print(f"{Fore.YELLOW}🌐 PASO 3: Verificando configuración de Proxies...")
        
        try:
            instagram_config = self.scrapfly_config.platform_configs.get('instagram', {})
            
            # Verificar proxy pool
            proxy_pool = instagram_config.get('proxy_pool', '')
            if proxy_pool == 'public_residential_pool':
                self._add_result("✅", "Proxy Pool", "Residencial (recomendado)")
            elif 'residential' in proxy_pool.lower():
                self._add_result("✅", "Proxy Pool", f"Residencial: {proxy_pool}")
            elif 'datacenter' in proxy_pool.lower():
                self._add_result("❌", "Proxy Pool", "Datacenter (bloqueado por Instagram)")
            else:
                self._add_result("⚠️", "Proxy Pool", f"No especificado: {proxy_pool}")
            
            # Verificar país
            country = instagram_config.get('country', 'US')
            recommended_countries = ['US', 'CA', 'GB', 'DE']
            if country in recommended_countries:
                self._add_result("✅", "País Proxy", f"{country} (recomendado)")
            else:
                self._add_result("⚠️", "País Proxy", f"{country} (no optimizado)")
                
        except Exception as e:
            self._add_result("❌", "Proxy Config", f"Error: {str(e)}")
    
    def _validate_instagram_headers(self):
        """✅ Paso 4: Verificar headers críticos de Instagram"""
        print(f"{Fore.YELLOW}📋 PASO 4: Verificando Headers de Instagram...")
        
        try:
            instagram_config = self.scrapfly_config.platform_configs.get('instagram', {})
            headers = instagram_config.get('additional_headers', {})
            
            # Verificar x-ig-app-id (CRÍTICO)
            x_ig_app_id = headers.get('x-ig-app-id', '')
            if x_ig_app_id == '936619743392459':
                self._add_result("✅", "x-ig-app-id", "Header crítico presente")
            elif x_ig_app_id:
                self._add_result("⚠️", "x-ig-app-id", f"Valor no estándar: {x_ig_app_id}")
            else:
                self._add_result("❌", "x-ig-app-id", "FALTA header crítico")
            
            # Verificar otros headers importantes
            required_headers = {
                'User-Agent': 'Mozilla/5.0',
                'Accept': '*/*',
                'Referer': 'https://www.instagram.com/',
                'Origin': 'https://www.instagram.com'
            }
            
            for header_name, expected_content in required_headers.items():
                header_value = headers.get(header_name, '')
                if expected_content in header_value:
                    self._add_result("✅", f"{header_name}", "Presente")
                else:
                    self._add_result("⚠️", f"{header_name}", "Falta o incorrecto")
                    
        except Exception as e:
            self._add_result("❌", "Headers", f"Error: {str(e)}")
    
    def _validate_timeout_configuration(self):
        """✅ Paso 5: Verificar timeouts"""
        print(f"{Fore.YELLOW}⏰ PASO 5: Verificando configuración de Timeouts...")
        
        try:
            instagram_config = self.scrapfly_config.platform_configs.get('instagram', {})
            
            timeout = instagram_config.get('timeout', 0)
            if timeout >= 60000:  # 60+ segundos
                self._add_result("✅", "Timeout", f"{timeout/1000}s (adecuado para ASP)")
            elif timeout >= 30000:  # 30+ segundos
                self._add_result("⚠️", "Timeout", f"{timeout/1000}s (mínimo)")
            else:
                self._add_result("❌", "Timeout", f"{timeout/1000}s (insuficiente para ASP)")
                
        except Exception as e:
            self._add_result("❌", "Timeout Config", f"Error: {str(e)}")
    
    def _validate_session_management(self):
        """✅ Paso 6: Verificar manejo de sesiones"""
        print(f"{Fore.YELLOW}🔗 PASO 6: Verificando manejo de Sesiones...")
        
        try:
            # Crear config de prueba y verificar session
            test_config = self.scrapfly_config.create_scrape_config(
                "https://www.instagram.com/test", 
                'instagram'
            )
            
            session_id = getattr(test_config, 'session', None)
            
            if session_id and 'instagram-session' in session_id:
                self._add_result("✅", "Sesiones", "Configuración automática presente")
            else:
                self._add_result("⚠️", "Sesiones", "No configurado automáticamente")
                
        except Exception as e:
            self._add_result("❌", "Session Config", f"Error: {str(e)}")
    
    def _validate_retry_logic(self):
        """✅ Paso 7: Verificar retry logic"""
        print(f"{Fore.YELLOW}🔄 PASO 7: Verificando lógica de Retry...")
        
        try:
            instagram_config = self.scrapfly_config.platform_configs.get('instagram', {})
            
            # Verificar que retry esté habilitado
            retry_enabled = instagram_config.get('retry', False)
            if retry_enabled:
                self._add_result("✅", "Retry", "Habilitado")
            else:
                self._add_result("⚠️", "Retry", "No habilitado automáticamente")
            
            # Verificar que el método scrape_with_retry existe y es funcional
            if hasattr(self.scrapfly_config, 'scrape_with_retry'):
                self._add_result("✅", "Retry Logic", "Método implementado")
            else:
                self._add_result("❌", "Retry Logic", "Método no encontrado")
                
        except Exception as e:
            self._add_result("❌", "Retry Config", f"Error: {str(e)}")
    
    def _add_result(self, status, component, message):
        """Añadir resultado de validación"""
        color = Fore.GREEN if status == "✅" else Fore.YELLOW if status == "⚠️" else Fore.RED
        
        self.validation_results.append({
            'status': status,
            'component': component,
            'message': message,
            'color': color
        })
        
        print(f"  {color}{status} {component}: {message}")
    
    def _show_validation_summary(self):
        """Mostrar resumen final de validación"""
        print()
        print(f"{Fore.CYAN}{'='*70}")
        print(f"{Fore.CYAN}    RESUMEN DE VALIDACIÓN")
        print(f"{Fore.CYAN}{'='*70}")
        
        success_count = len([r for r in self.validation_results if r['status'] == '✅'])
        warning_count = len([r for r in self.validation_results if r['status'] == '⚠️'])
        error_count = len([r for r in self.validation_results if r['status'] == '❌'])
        total_count = len(self.validation_results)
        
        print(f"{Fore.GREEN}✅ Éxitos: {success_count}")
        print(f"{Fore.YELLOW}⚠️ Advertencias: {warning_count}")
        print(f"{Fore.RED}❌ Errores: {error_count}")
        print(f"{Fore.WHITE}📊 Total: {total_count}")
        print()
        
        # Determinar estado general
        if error_count == 0 and warning_count <= 2:
            print(f"{Fore.GREEN}🎉 CONFIGURACIÓN ÓPTIMA - Listo para Instagram scraping!")
            return True
        elif error_count <= 2:
            print(f"{Fore.YELLOW}⚠️ CONFIGURACIÓN FUNCIONAL - Puede funcionar con limitaciones")
            return True
        else:
            print(f"{Fore.RED}❌ CONFIGURACIÓN PROBLEMÁTICA - Requiere correcciones")
            
            print(f"\n{Fore.RED}🔧 ERRORES CRÍTICOS A CORREGIR:")
            for result in self.validation_results:
                if result['status'] == '❌':
                    print(f"  • {result['component']}: {result['message']}")
            
            return False

def main():
    """Función principal del validador"""
    validator = ScrapFlyValidator()
    success = validator.run_full_validation()
    
    print()
    if success:
        print(f"{Fore.GREEN}✅ Validación completada - Sistema listo para usar")
    else:
        print(f"{Fore.RED}❌ Validación fallida - Corrige errores antes de continuar")
        
    input(f"\n{Fore.WHITE}Presiona Enter para continuar...")
    return success

if __name__ == "__main__":
    main()