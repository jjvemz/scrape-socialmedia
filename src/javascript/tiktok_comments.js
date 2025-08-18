// TikTok Comment Scraper JavaScript
// Este script se ejecuta en el navegador para cargar todos los comentarios

(function() {
    'use strict';
    
    // Selectores CSS para TikTok
    const SELECTORS = {
        commentsList: 'div[data-e2e="comment-list"]',
        commentItems: '[data-e2e="comment-item"]',
        loadMoreButton: '[data-e2e="comment-load-more"]',
        viewRepliesButton: '[data-e2e="comment-reply-view"]',
        username: '[data-e2e="comment-username"]',
        commentText: '[data-e2e="comment-text"]',
        likeCount: '[data-e2e="comment-like-count"]',
        timeAgo: '[data-e2e="comment-time"]',
        profilePic: '[data-e2e="comment-avatar"] img'
    };
    
    // Función principal para cargar todos los comentarios
    async function loadAllComments() {
        console.log('🎵 Iniciando carga de comentarios de TikTok...');
        
        let previousCount = 0;
        let stableCount = 0;
        const maxStableIterations = 5;
        let totalLoaded = 0;
        
        // Esperar a que aparezca la lista de comentarios
        await waitForElement(SELECTORS.commentsList, 10000);
        
        while (stableCount < maxStableIterations) {
            // 1. Scroll hacia abajo para activar lazy loading
            await scrollToBottom();
            
            // 2. Buscar y hacer clic en botones "Load more" o "View more"
            await clickLoadMoreButtons();
            
            // 3. Expandir respuestas a comentarios
            await expandReplies();
            
            // 4. Contar comentarios actuales
            const currentComments = document.querySelectorAll(SELECTORS.commentItems);
            const currentCount = currentComments.length;
            
            console.log(`📊 Comentarios cargados: ${currentCount}`);
            
            // 5. Verificar si se cargaron nuevos comentarios
            if (currentCount === previousCount) {
                stableCount++;
                console.log(`⏳ Sin cambios (${stableCount}/${maxStableIterations})`);
            } else {
                stableCount = 0;
                previousCount = currentCount;
                totalLoaded = currentCount;
            }
            
            // 6. Pausa entre iteraciones
            await sleep(2000);
        }
        
        console.log(`✅ Carga completada. Total de comentarios: ${totalLoaded}`);
        return {
            success: true,
            totalComments: totalLoaded,
            html: document.documentElement.outerHTML
        };
    }
    
    // Función para hacer scroll suave hacia abajo
    async function scrollToBottom() {
        const scrollHeight = document.body.scrollHeight;
        const currentScroll = window.pageYOffset + window.innerHeight;
        
        if (currentScroll < scrollHeight) {
            window.scrollTo({
                top: scrollHeight,
                behavior: 'smooth'
            });
            await sleep(1000);
        }
    }
    
    // Función para hacer clic en botones de "cargar más"
    async function clickLoadMoreButtons() {
        // Buscar botones de "load more" o similares
        const loadMoreButtons = document.querySelectorAll(
            `${SELECTORS.loadMoreButton}, ` +
            'button:not([disabled]), ' +
            '[role="button"]:not([disabled])'
        );
        
        let clicked = false;
        
        for (const button of loadMoreButtons) {
            const buttonText = button.textContent.toLowerCase();
            
            // Verificar si es un botón de cargar más
            if (isLoadMoreButton(buttonText) && isElementVisible(button)) {
                console.log(`🔄 Haciendo clic en: "${button.textContent.trim()}"`);
                
                try {
                    button.click();
                    clicked = true;
                    await sleep(1500); // Esperar a que cargue
                } catch (error) {
                    console.warn('⚠️ Error haciendo clic:', error);
                }
            }
        }
        
        return clicked;
    }
    
    // Función para expandir respuestas a comentarios
    async function expandReplies() {
        const replyButtons = document.querySelectorAll(
            `${SELECTORS.viewRepliesButton}, ` +
            '[data-e2e*="reply"], ' +
            'button, [role="button"]'
        );
        
        let expanded = 0;
        
        for (const button of replyButtons) {
            const buttonText = button.textContent.toLowerCase();
            
            if (isReplyButton(buttonText) && isElementVisible(button)) {
                try {
                    button.click();
                    expanded++;
                    await sleep(800);
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
            'load more', 'view more', 'see more', 'show more',
            'cargar más', 'ver más', 'mostrar más',
            'load', 'more comments', 'más comentarios'
        ];
        
        return loadMoreKeywords.some(keyword => text.includes(keyword));
    }
    
    // Función para verificar si un botón es de respuestas
    function isReplyButton(text) {
        const replyKeywords = [
            'view repl', 'show repl', 'see repl',
            'ver respuesta', 'mostrar respuesta',
            'replies', 'respuestas'
        ];
        
        return replyKeywords.some(keyword => text.includes(keyword));
    }
    
    // Función para verificar si un elemento es visible
    function isElementVisible(element) {
        if (!element || !element.offsetParent) return false;
        
        const rect = element.getBoundingClientRect();
        return rect.width > 0 && rect.height > 0;
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
    
    // Función para extraer datos de comentarios (opcional, para debugging)
    function extractCommentData() {
        const comments = [];
        const commentElements = document.querySelectorAll(SELECTORS.commentItems);
        
        commentElements.forEach((element, index) => {
            try {
                const usernameEl = element.querySelector(SELECTORS.username);
                const textEl = element.querySelector(SELECTORS.commentText);
                const likesEl = element.querySelector(SELECTORS.likeCount);
                const timeEl = element.querySelector(SELECTORS.timeAgo);
                const profilePicEl = element.querySelector(SELECTORS.profilePic);
                
                const comment = {
                    id: index + 1,
                    username: usernameEl ? usernameEl.textContent.trim() : '',
                    text: textEl ? textEl.textContent.trim() : '',
                    likes: likesEl ? likesEl.textContent.trim() : '0',
                    timeAgo: timeEl ? timeEl.textContent.trim() : '',
                    profilePic: profilePicEl ? profilePicEl.src : '',
                    isReply: element.closest('[data-e2e*="reply"]') !== null
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
    
    // Exportar funciones para uso externo
    window.TikTokScraper = {
        loadAllComments,
        extractCommentData,
        SELECTORS
    };
    
    // Auto-ejecutar si se carga directamente
    if (typeof module === 'undefined' && typeof window !== 'undefined') {
        console.log('📱 TikTok Comment Scraper cargado');
    }
    
})();