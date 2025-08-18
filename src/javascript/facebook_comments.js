// Facebook Comment Scraper JavaScript
// Este script se ejecuta en el navegador para cargar todos los comentarios

(function() {
    'use strict';
    
    // Selectores CSS para Facebook (pueden cambiar frecuentemente)
    const SELECTORS = {
        commentsContainer: '[role="main"], [data-pagelet*="comment"]',
        commentItems: '[data-testid*="comment"], [role="article"] [role="article"]',
        loadMoreButton: 'div[role="button"], span[role="button"]',
        userLink: 'a[href*="facebook.com"]',
        profilePic: 'img[src*="profile"]',
        timeElement: 'time, abbr[data-utime]',
        reactionButton: '[aria-label*="like"], [aria-label*="reaction"]'
    };
    
    // Función principal para cargar todos los comentarios
    async function loadAllComments() {
        console.log('📘 Iniciando carga de comentarios de Facebook...');
        
        let previousCount = 0;
        let stableCount = 0;
        const maxStableIterations = 8;
        let totalLoaded = 0;
        let attempts = 0;
        const maxAttempts = 30;
        
        // Esperar a que aparezca el contenido principal
        await waitForElement('[role="main"]', 10000);
        
        while (stableCount < maxStableIterations && attempts < maxAttempts) {
            attempts++;
            
            // 1. Buscar y hacer clic en botones "View more comments"
            const loadedMore = await clickLoadMoreButtons();
            
            // 2. Expandir respuestas a comentarios
            const expandedReplies = await expandReplies();
            
            // 3. Scroll para activar lazy loading
            await scrollToLoadComments();
            
            // 4. Contar comentarios actuales
            const currentComments = getValidComments();
            const currentCount = currentComments.length;
            
            console.log(`📊 Comentarios cargados: ${currentCount} (intento ${attempts})`);
            
            // 5. Verificar progreso
            if (currentCount === previousCount && !loadedMore && !expandedReplies) {
                stableCount++;
                console.log(`⏳ Sin cambios (${stableCount}/${maxStableIterations})`);
            } else {
                stableCount = 0;
                previousCount = currentCount;
                totalLoaded = currentCount;
            }
            
            // 6. Pausa más larga para Facebook
            await sleep(3000);
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
        // Buscar elementos que parezcan comentarios
        const potentialComments = document.querySelectorAll(
            '[data-testid*="comment"], ' +
            '[role="article"] [role="article"], ' +
            'div[data-sigil="comment"], ' +
            '.UFIComment'
        );
        
        const validComments = [];
        
        potentialComments.forEach(element => {
            // Verificar que tiene enlace de usuario y contenido de texto
            const userLink = element.querySelector('a[href*="facebook.com"]');
            const hasText = element.textContent.trim().length > 10;
            
            if (userLink && hasText && isValidFacebookUserLink(userLink.href)) {
                validComments.push(element);
            }
        });
        
        // Si no encontramos comentarios específicos, buscar de forma más general
        if (validComments.length === 0) {
            const generalElements = document.querySelectorAll('div');
            
            generalElements.forEach(element => {
                const userLink = element.querySelector('a[href*="facebook.com"]');
                const textContent = element.textContent.trim();
                
                if (userLink && 
                    textContent.length > 10 && 
                    textContent.length < 1000 && // No demasiado largo
                    isValidFacebookUserLink(userLink.href) &&
                    !element.querySelector('video, img[src*="video"]')) { // No elementos de video
                    
                    validComments.push(element);
                }
            });
        }
        
        // Eliminar duplicados basándose en contenido de texto
        const uniqueComments = [];
        const seenTexts = new Set();
        
        validComments.forEach(comment => {
            const text = comment.textContent.trim().substring(0, 100);
            if (!seenTexts.has(text)) {
                seenTexts.add(text);
                uniqueComments.push(comment);
            }
        });
        
        return uniqueComments;
    }
    
    // Función para verificar si un enlace es de usuario válido de Facebook
    function isValidFacebookUserLink(href) {
        if (!href) return false;
        
        // Verificar que es un enlace de perfil válido
        const patterns = [
            /^https?:\/\/[^\/]*facebook\.com\/[^\/\?]+\/?$/,
            /^https?:\/\/[^\/]*facebook\.com\/profile\.php\?id=\d+/,
            /^https?:\/\/[^\/]*facebook\.com\/[^\/]+\?/
        ];
        
        const isValid = patterns.some(pattern => pattern.test(href));
        
        // Excluir URLs que no son perfiles
        const excludePatterns = [
            '/pages/', '/groups/', '/events/', '/photo/', '/video/',
            '/watch/', '/marketplace/', '/gaming/', '/business/'
        ];
        
        const isExcluded = excludePatterns.some(pattern => href.includes(pattern));
        
        return isValid && !isExcluded;
    }
    
    // Función para hacer scroll y cargar comentarios
    async function scrollToLoadComments() {
        // Scroll hacia abajo en increments
        const scrollStep = window.innerHeight * 0.8;
        window.scrollBy({ top: scrollStep, behavior: 'smooth' });
        
        await sleep(2000);
        
        // Scroll adicional al final de la página
        const isNearBottom = window.innerHeight + window.pageYOffset >= document.body.offsetHeight - 1000;
        
        if (isNearBottom) {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
            await sleep(1500);
        }
    }
    
    // Función para hacer clic en botones de "cargar más"
    async function clickLoadMoreButtons() {
        const buttons = document.querySelectorAll(
            'div[role="button"], span[role="button"], a[role="button"]'
        );
        
        let clicked = false;
        
        for (const button of buttons) {
            const buttonText = button.textContent.toLowerCase();
            
            if (isLoadMoreButton(buttonText) && isElementVisible(button)) {
                console.log(`🔄 Haciendo clic en: "${button.textContent.trim()}"`);
                
                try {
                    // Hacer scroll al botón
                    button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    await sleep(1000);
                    
                    // Intentar hacer clic
                    button.click();
                    clicked = true;
                    await sleep(4000); // Esperar más tiempo para Facebook
                    
                    // Límite de clics para evitar loops
                    break;
                } catch (error) {
                    console.warn('⚠️ Error haciendo clic:', error);
                }
            }
        }
        
        return clicked;
    }
    
    // Función para expandir respuestas a comentarios
    async function expandReplies() {
        const buttons = document.querySelectorAll(
            'div[role="button"], span[role="button"], a[role="button"]'
        );
        
        let expanded = 0;
        const maxExpansions = 15; // Límite para evitar loops infinitos
        
        for (const button of buttons) {
            if (expanded >= maxExpansions) break;
            
            const buttonText = button.textContent.toLowerCase();
            
            if (isReplyButton(buttonText) && isElementVisible(button)) {
                try {
                    button.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    await sleep(800);
                    
                    button.click();
                    expanded++;
                    await sleep(2000);
                } catch (error) {
                    console.warn('⚠️ Error expandiendo respuestas:', error);
                }
            }
        }
        
        if (expanded > 0) {
            console.log(`💬 Expandidas ${expanded} respuestas`);
        }
        
        return expanded > 0;
    }
    
    // Función para verificar si un botón es de "cargar más"
    function isLoadMoreButton(text) {
        const loadMoreKeywords = [
            'view more comments',
            'see more comments',
            'load more comments',
            'show more comments',
            'view previous comments',
            'ver más comentarios',
            'cargar más comentarios',
            'mostrar más comentarios',
            'ver comentarios anteriores',
            'more comments',
            'más comentarios'
        ];
        
        return loadMoreKeywords.some(keyword => text.includes(keyword));
    }
    
    // Función para verificar si un botón es de respuestas
    function isReplyButton(text) {
        const replyKeywords = [
            'view replies',
            'show replies',
            'see replies',
            'view all replies',
            'ver respuestas',
            'mostrar respuestas',
            'ver todas las respuestas',
            'replies',
            'respuestas'
        ];
        
        // Excluir botones de "Hide replies"
        const hideKeywords = ['hide', 'ocultar'];
        
        return replyKeywords.some(keyword => text.includes(keyword)) &&
               !hideKeywords.some(keyword => text.includes(keyword));
    }
    
    // Función para verificar si un elemento es visible
    function isElementVisible(element) {
        if (!element || element.offsetParent === null) return false;
        
        const rect = element.getBoundingClientRect();
        const isInViewport = rect.top >= 0 && 
                           rect.left >= 0 && 
                           rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                           rect.right <= (window.innerWidth || document.documentElement.clientWidth);
        
        return rect.width > 0 && rect.height > 0 && isInViewport;
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
                const userLink = element.querySelector('a[href*="facebook.com"]');
                const timeElement = element.querySelector('time, abbr[data-utime]');
                const profilePic = element.querySelector('img[src*="profile"]');
                
                // Extraer username de la URL
                let username = '';
                if (userLink) {
                    const href = userLink.href;
                    const usernameMatch = href.match(/facebook\.com\/([^\/\?]+)/);
                    if (usernameMatch) {
                        username = usernameMatch[1];
                    }
                }
                
                // Extraer texto del comentario
                const userLinkText = userLink ? userLink.textContent.trim() : '';
                let commentText = element.textContent.trim();
                
                // Remover el nombre del usuario del texto del comentario
                if (userLinkText && commentText.startsWith(userLinkText)) {
                    commentText = commentText.substring(userLinkText.length).trim();
                }
                
                // Extraer tiempo
                let timePosted = '';
                if (timeElement) {
                    timePosted = timeElement.getAttribute('data-utime') || 
                                timeElement.getAttribute('datetime') || 
                                timeElement.textContent.trim();
                }
                
                const comment = {
                    id: index + 1,
                    username: username,
                    displayName: userLinkText,
                    text: commentText,
                    timePosted: timePosted,
                    profilePic: profilePic ? profilePic.src : '',
                    userUrl: userLink ? userLink.href : ''
                };
                
                if (comment.username && comment.text && comment.text.length > 5) {
                    comments.push(comment);
                }
            } catch (error) {
                console.warn(`⚠️ Error extrayendo comentario ${index}:`, error);
            }
        });
        
        return comments;
    }
    
    // Función para detectar el tipo de contenido
    function detectContentType() {
        const url = window.location.href;
        
        if (url.includes('/watch?v=')) return 'video';
        if (url.includes('/videos/')) return 'video';
        if (url.includes('/posts/')) return 'post';
        if (url.includes('/photo/')) return 'photo';
        if (url.includes('fb.watch/')) return 'video';
        
        return 'unknown';
    }
    
    // Función para obtener metadatos del post/video
    function extractPostMetadata() {
        const metadata = {
            url: window.location.href,
            contentType: detectContentType(),
            timestamp: new Date().toISOString()
        };
        
        // Intentar extraer datos del título
        const title = document.title;
        if (title && title !== 'Facebook') {
            metadata.title = title;
        }
        
        // Intentar extraer autor desde meta tags
        const authorMeta = document.querySelector('meta[property="og:title"]');
        if (authorMeta) {
            metadata.author = authorMeta.content;
        }
        
        return metadata;
    }
    
    // Exportar funciones para uso externo
    window.FacebookScraper = {
        loadAllComments,
        extractCommentData,
        extractPostMetadata,
        detectContentType,
        SELECTORS
    };
    
    // Auto-ejecutar si se carga directamente
    if (typeof module === 'undefined' && typeof window !== 'undefined') {
        console.log('📱 Facebook Comment Scraper cargado');
    }
    
})();