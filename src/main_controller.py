#!/usr/bin/env python3
"""
Social Media Scraper - Controlador Principal
Permite scraping de comentarios de TikTok, Instagram y Facebook
"""

import os
import sys
import time
from datetime import datetime
from colorama import Fore, Style, init
from tqdm import tqdm

# Añadir el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.url_validator import URLValidator
from utils.file_handler import FileHandler
from utils.scrapfly_config import ScrapFlyConfig
from tiktok_scraper import TikTokScraper
from instagram_scraper import InstagramScraper  
from facebook_scraper import FacebookScraper

# Inicializar colorama para Windows
init(autoreset=True)

class SocialMediaController:
    def __init__(self):
        self.validator = URLValidator()
        self.file_handler = FileHandler()
        self.scrapers = {
            'tiktok': TikTokScraper(),
            'instagram': InstagramScraper(),
            'facebook': FacebookScraper()
        }
        self.results = []
        
    def print_banner(self):
        """Muestra el banner de la aplicación"""
        print(f"{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}    SOCIAL MEDIA SCRAPER v1.0")
        print(f"{Fore.CYAN}    Extractor de comentarios para TikTok, Instagram y Facebook")
        print(f"{Fore.CYAN}{'='*60}")
        print()
        
    def get_user_input(self):
        """Obtiene la entrada del usuario"""
        print(f"{Fore.YELLOW}Plataformas disponibles:")
        print(f"{Fore.WHITE}1. TikTok")
        print(f"{Fore.WHITE}2. Instagram") 
        print(f"{Fore.WHITE}3. Facebook")
        print()
        
        # Selección de plataforma
        while True:
            try:
                platform_choice = input(f"{Fore.GREEN}Selecciona la plataforma (1-3): {Style.RESET_ALL}")
                platform_map = {'1': 'tiktok', '2': 'instagram', '3': 'facebook'}
                
                if platform_choice in platform_map:
                    platform = platform_map[platform_choice]
                    break
                else:
                    print(f"{Fore.RED}ERROR: Selección inválida. Ingresa 1, 2 o 3.")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}ERROR: Proceso cancelado por el usuario.")
                sys.exit(0)
        
        # Número de URLs
        while True:
            try:
                num_urls = int(input(f"{Fore.GREEN}¿Cuántos videos quieres procesar? (1-10): {Style.RESET_ALL}"))
                if 1 <= num_urls <= 10:
                    break
                else:
                    print(f"{Fore.RED}ERROR: Debe ser entre 1 y 10 videos.")
            except ValueError:
                print(f"{Fore.RED}ERROR: Ingresa un número válido.")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}ERROR: Proceso cancelado por el usuario.")
                sys.exit(0)
        
        # Recolección de URLs
        urls = []
        print(f"\n{Fore.YELLOW}Ingresa las URLs de {platform.upper()}:")
        
        for i in range(num_urls):
            while True:
                try:
                    url = input(f"{Fore.WHITE}URL {i+1}: {Style.RESET_ALL}").strip()
                    
                    if self.validator.is_valid_url(url, platform):
                        urls.append(url)
                        print(f"{Fore.GREEN}OK: URL válida")
                        break
                    else:
                        print(f"{Fore.RED}ERROR: URL inválida para {platform}. Intenta de nuevo.")
                except KeyboardInterrupt:
                    print(f"\n{Fore.YELLOW}ERROR: Proceso cancelado por el usuario.")
                    sys.exit(0)
        
        # Formato de salida
        while True:
            try:
                format_choice = input(f"\n{Fore.GREEN}Formato de salida (excel/csv): {Style.RESET_ALL}").lower().strip()
                if format_choice in ['excel', 'csv']:
                    break
                else:
                    print(f"{Fore.RED}ERROR: Ingresa 'excel' o 'csv'.")
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}ERROR: Proceso cancelado por el usuario.")
                sys.exit(0)
        
        return platform, urls, format_choice
    
    def process_urls(self, platform, urls, output_format):
        """Procesa las URLs y extrae los comentarios"""
        print(f"\n{Fore.CYAN}Iniciando scraping de {len(urls)} video(s) de {platform.upper()}...")
        print()
        
        scraper = self.scrapers[platform]
        failed_urls = []
        
        for i, url in enumerate(urls, 1):
            print(f"{Fore.YELLOW}Procesando video {i}/{len(urls)}: {url[:50]}...")
            
            try:
                # Crear barra de progreso
                with tqdm(total=100, desc=f"Video {i}", bar_format='{l_bar}{bar}| {n_fmt}%') as pbar:
                    
                    # Simular progreso durante el scraping
                    pbar.update(20)
                    result = scraper.scrape_comments(url)
                    pbar.update(30)
                    
                    if result['success']:
                        pbar.update(50)
                        # Procesar datos
                        processed_data = self._process_video_data(result['data'], platform, url)
                        self.results.append(processed_data)
                        pbar.update(100)
                        
                        print(f"{Fore.GREEN}OK: Video {i} completado: {result['data']['total_comments']} comentarios extraídos")
                    else:
                        failed_urls.append(url)
                        pbar.update(100)
                        print(f"{Fore.RED}ERROR: Error en video {i}: {result.get('error', 'Error desconocido')}")
                
            except Exception as e:
                failed_urls.append(url)
                print(f"{Fore.RED}ERROR: Error inesperado en video {i}: {str(e)}")
            
            # Pausa entre requests para evitar rate limiting
            if i < len(urls):
                print(f"{Fore.BLUE}Esperando 2 segundos antes del siguiente video...")
                time.sleep(2)
        
        # Reporte final
        print(f"\n{Fore.CYAN}REPORTE FINAL:")
        print(f"{Fore.GREEN}OK: Videos exitosos: {len(self.results)}/{len(urls)}")
        if failed_urls:
            print(f"{Fore.RED}ERROR: Videos fallidos: {len(failed_urls)}")
            for url in failed_urls:
                print(f"   • {url[:50]}...")
        
        return len(self.results) > 0
    
    def _process_video_data(self, video_data, platform, url):
        """Procesa y estructura los datos del video"""
        return {
            'platform': platform,
            'url': url,
            'metadata': video_data.get('metadata', {}),
            'comments': video_data.get('comments', []),
            'timestamp': datetime.now()
        }
    
    def save_results(self, platform, output_format):
        """Guarda los resultados en el formato seleccionado"""
        if not self.results:
            print(f"{Fore.RED}ERROR: No hay datos para guardar.")
            return
            
        print(f"\n{Fore.CYAN}Guardando resultados en formato {output_format.upper()}...")
        
        # Crear nombre de archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{platform}_{timestamp}"
        
        try:
            if output_format == 'excel':
                filepath = self.file_handler.save_to_excel(self.results, platform, filename)
            else:
                filepath = self.file_handler.save_to_csv(self.results, platform, filename)
            
            print(f"{Fore.GREEN}OK: Archivo guardado exitosamente:")
            print(f"{Fore.WHITE}   {filepath}")
            
            # Estadísticas finales
            total_comments = sum(len(result['comments']) for result in self.results)
            print(f"\n{Fore.CYAN}ESTADÍSTICAS:")
            print(f"{Fore.WHITE}   Videos procesados: {len(self.results)}")
            print(f"{Fore.WHITE}   Total de comentarios: {total_comments}")
            print(f"{Fore.WHITE}   Formato: {output_format.upper()}")
            
        except Exception as e:
            print(f"{Fore.RED}ERROR: Error al guardar archivo: {str(e)}")
    
    def run(self):
        """Ejecuta el flujo principal de la aplicación"""
        try:
            self.print_banner()
            
            # Verificar configuración de ScrapFly
            config = ScrapFlyConfig()
            if not config.verify_connection():
                print(f"{Fore.RED}ERROR: Error en la configuración de ScrapFly. Verifica tu API key.")
                input("Presiona Enter para continuar...")
                return
            
            # Obtener input del usuario
            platform, urls, output_format = self.get_user_input()
            
            # Procesar URLs
            success = self.process_urls(platform, urls, output_format)
            
            # Guardar resultados
            if success:
                self.save_results(platform, output_format)
            else:
                print(f"{Fore.RED}ERROR: No se pudo procesar ningún video exitosamente.")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}ERROR: Proceso interrumpido por el usuario.")
        except Exception as e:
            print(f"{Fore.RED}ERROR: Error inesperado: {str(e)}")
        finally:
            print(f"\n{Fore.CYAN}Gracias por usar Social Media Scraper!")
            input("Presiona Enter para salir...")

def main():
    controller = SocialMediaController()
    controller.run()

if __name__ == "__main__":
    main()