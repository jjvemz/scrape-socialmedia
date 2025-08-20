// Instagram Comment Scraper JavaScript
// Este script se ejecuta en el navegador para cargar todos los comentarios

(function() {
    'use strict';
    
    // Selectores CSS para Instagram
    const SELECTORS = {
        commentsList: 'article section ul',
        commentItems: 'article section ul li',
        loadMoreButton: 'button[type="button"]',
        userLink: 'a[href^="/"]',
        commentText: 'span',
        timeElement: 'time',
        likeButton: 'button[aria-label*="like"]',
        profilePic: 'img[alt*="profile picture"]'
    };
    
    // Función principal para cargar todos los comentarios
    async function loadAllComments() {
        console.log('📸 Iniciando carga de comentarios de Instagram...');
        
        let previousCount = 0;
        let stableCount = 0;
        const maxStableIterations = 6;
        let totalLoaded = 0;
        
        // Esperar a que aparezca la sección de comentarios
        await waitForElement('article section', 8000);
        
        while (stableCount < maxStableIterations) {
            // 1. Buscar y hacer clic en botones "Load more comments"
            const loadedMore = await clickLoadMoreButtons();
            
            // 2. Scroll suave hacia abajo
            await scrollToLoadComments();
            
            // 3. Expandir respuestas a comentarios
            await expandReplies();
            
            // 4. Contar comentarios actuales
            const currentComments = getValidComments();
            const currentCount = currentComments.length;
            
            console.log(`📊 Comentarios cargados: ${currentCount}`);
            
            // 5. Verificar progreso
            if (currentCount === previousCount && !loadedMore) {
                stableCount++;
                console.log(`⏳ Sin cambios (${stableCount}/${maxStableIterations})`);
            } else {
                stableCount = 0;
                previousCount = currentCount;
                totalLoaded = currentCount;
            }
            
            // 6. Pausa entre iteraciones
            await sleep(3500);
        }
        
        console.log(`✅ Carga completada. Total de comentarios: ${totalLoaded}`);
        return {
            success: true,
            totalComments: totalLoaded,
            html: document.documentElement.outerHTML
        };
    }
    
    // Función para obtener comentarios válidos
    function getValidComments() {
        const commentElements = document.querySelectorAll(SELECTORS.commentItems);
        const validComments = [];
        
        commentElements.forEach(element => {
            // Verificar que tiene enlace de usuario y texto
            const userLink = element.querySelector(SELECTORS.userLink);
            const hasText = element.textContent.trim().length > 0;
            
            if (userLink && hasText && isValidUserLink(userLink.href)) {
                validComments.push(element);
            }
        });
        
        return validComments;
    }
    
    // Función para verificar si un enlace es de usuario válido
    function isValidUserLink(href) {
        if (!href) return false;
        
        // Verificar que es un enlace de perfil de usuario
        const userPattern = /^https?:\/\/[^\/]*instagram\.com\/[^\/]+\/?$/;
        return userPattern.test(href) && 
               !href.includes('/p/') && 
               !href.includes('/reel/') &&
               !href.includes('/tv/');
    }
    
    // Función para hacer scroll y cargar comentarios
    async function scrollToLoadComments() {
        // Instagram carga comentarios con scroll más suave
        const commentsSection = document.querySelector('article section');
        
        if (commentsSection) {
            commentsSection.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'end' 
            });
            await sleep(1000);
        }
        
        // Scroll general hacia abajo
        window.scrollBy({ 
            top: window.innerHeight * 0.5, 
            behavior: 'smooth' 
        });
        
        await sleep(1500);
    }
    
    // Función para hacer clic en botones de "cargar más"
    async function clickLoadMoreButtons() {
        const buttons = document.querySelectorAll(SELECTORS.loadMoreButton);
        let clicked = false;
        
        for (const button of buttons) {
            const buttonText = button.textContent.toLowerCase();
            
            if (isLoadMoreButton(buttonText) && isElementVisible(button) && !button.disabled) {
                console.log(`🔄 Haciendo clic en: "${button.textContent.trim()}"`);
                
                try {
                    // Scroll al botón primero
                    button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    await sleep(500);
                    
                    button.click();
                    clicked = true;
                    await sleep(5000); // Esperar más tiempo para Instagram
                } catch (error) {
                    console.warn('⚠️ Error haciendo clic:', error);
                }
            }
        }
        
        return clicked;
    }
    
    // Función para expandir respuestas a comentarios
    async function expandReplies() {
        // Instagram usa botones de "View replies" o "Hide replies"
        const replyButtons = document.querySelectorAll('button[type="button"]');
        let expanded = 0;
        
        for (const button of replyButtons) {
            const buttonText = button.textContent.toLowerCase();
            
            if (isReplyButton(buttonText) && isElementVisible(button) && !button.disabled) {
                try {
                    button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    await sleep(300);
                    
                    button.click();
                    expanded++;
                    await sleep(2500);
                    
                    // Límite de respuestas para evitar loops infinitos
                    if (expanded >= 20) break;
                } catch (error) {
                    console.warn('⚠️ Error expandiendo respuestas:', error);
                }
            }
        }
        
        if (expanded > 0) {
            console.log(`💬 Expandidas ${expanded} respuestas`);
        }
        
        return expanded;
    }
    
    // Función para verificar si un botón es de "cargar más"
    function isLoadMoreButton(text) {
        const loadMoreKeywords = [
            'view more comments',
            'load more comments', 
            'view all',
            'see more',
            'show more',
            'ver más comentarios',
            'cargar más',
            'ver todos'
        ];
        
        return loadMoreKeywords.some(keyword => text.includes(keyword));
    }
    
    // Función para verificar si un botón es de respuestas
    function isReplyButton(text) {
        const replyKeywords = [
            'view replies',
            'view all replies',
            'show replies',
            'ver respuestas',
            'mostrar respuestas'
        ];
        
        // Excluir "Hide replies" ya que indica que están expandidas
        const hideKeywords = ['hide', 'ocultar'];
        
        return replyKeywords.some(keyword => text.includes(keyword)) &&
               !hideKeywords.some(keyword => text.includes(keyword));
    }
    
    // Función para verificar si un elemento es visible
    function isElementVisible(element) {
        if (!element || !element.offsetParent) return false;
        
        const rect = element.getBoundingClientRect();
        const viewport = {
            width: window.innerWidth || document.documentElement.clientWidth,
            height: window.innerHeight || document.documentElement.clientHeight
        };
        
        return rect.width > 0 && 
               rect.height > 0 && 
               rect.top >= 0 && 
               rect.left >= 0 && 
               rect.bottom <= viewport.height && 
               rect.right <= viewport.width;
    }
    
    // Función para esperar a que aparezca un elemento
    function waitForElement(selector, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const element = document.querySelector(selector);
            
            if (element) {
                resolve(element);
                return;
            }
            
            const observer = new MutationObserver((mutations, obs) => {
                const element = document.querySelector(selector);
                if (element) {
                    obs.disconnect();
                    resolve(element);
                }
            });
            
            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            setTimeout(() => {
                observer.disconnect();
                reject(new Error(`Timeout esperando elemento: ${selector}`));
            }, timeout);
        });
    }
    
    // Función para pausar ejecución
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Función para extraer datos de comentarios (para debugging)
    function extractCommentData() {
        const comments = [];
        const validComments = getValidComments();
        
        validComments.forEach((element, index) => {
            try {
                const userLink = element.querySelector(SELECTORS.userLink);
                const timeElement = element.querySelector(SELECTORS.timeElement);
                const profilePic = element.querySelector(SELECTORS.profilePic);
                
                // Extraer username de la URL
                const username = userLink ? userLink.href.split('/').filter(p => p).pop() : '';
                
                // Extraer texto del comentario
                let commentText = '';
                const textElements = element.querySelectorAll('span');
                for (const span of textElements) {
                    const text = span.textContent.trim();
                    if (text && text !== username && text.length > 2) {
                        commentText = text;
                        break;
                    }
                }
                
                // Extraer tiempo
                const timePosted = timeElement ? 
                    (timeElement.getAttribute('datetime') || timeElement.textContent.trim()) : '';
                
                const comment = {
                    id: index + 1,
                    username: username,
                    text: commentText,
                    timePosted: timePosted,
                    profilePic: profilePic ? profilePic.src : '',
                    userUrl: userLink ? userLink.href : '',
                    isReply: element.closest('ul') && element.closest('ul').closest('li') !== null
                };
                
                if (comment.username && comment.text) {
                    comments.push(comment);
                }
            } catch (error) {
                console.warn(`⚠️ Error extrayendo comentario ${index}:`, error);
            }
        });
        
        return comments;
    }
    
    // Función para detectar si estamos en un post o reel
    function detectContentType() {
        const url = window.location.href;
        
        if (url.includes('/p/')) return 'post';
        if (url.includes('/reel/')) return 'reel';
        if (url.includes('/tv/')) return 'tv';
        
        return 'unknown';
    }
    
    // Función para obtener metadatos del post
    function extractPostMetadata() {
        const metadata = {
            url: window.location.href,
            contentType: detectContentType(),
            timestamp: new Date().toISOString()
        };
        
        // Intentar extraer datos del título
        const title = document.title;
        if (title) {
            const usernameMatch = title.match(/@(\w+)/);
            if (usernameMatch) {
                metadata.username = usernameMatch[1];
            }
        }
        
        // Intentar extraer likes
        const likeElements = document.querySelectorAll('button[aria-label*="like"]');
        for (const element of likeElements) {
            const ariaLabel = element.getAttribute('aria-label') || '';
            const likesMatch = ariaLabel.match(/(\d+)/);
            if (likesMatch) {
                metadata.likes = parseInt(likesMatch[1]);
                break;
            }
        }
        
        return metadata;
    }
    
    // Exportar funciones para uso externo
    window.InstagramScraper = {
        loadAllComments,
        extractCommentData,
        extractPostMetadata,
        detectContentType,
        SELECTORS
    };
    
    // Auto-ejecutar si se carga directamente
    if (typeof module === 'undefined' && typeof window !== 'undefined') {
        console.log('📱 Instagram Comment Scraper cargado');
    }
    
})();