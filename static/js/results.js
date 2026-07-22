document.addEventListener('DOMContentLoaded', () => {
    const loadingSpinner = document.getElementById('loading-spinner');
    const resultsContainer = document.getElementById('results-container');
    const errorContainer = document.getElementById('error-container');
    const startOverBar = document.getElementById('start-over-bar');
    const statusText = document.getElementById('status-text');

    // Read results from sessionStorage
    const savedResults = sessionStorage.getItem('quiz_results');
    let recommendations = [];
    
    if (savedResults) {
        try {
            recommendations = JSON.parse(savedResults);
        } catch (e) {
            console.error("Error parsing results:", e);
        }
    }
    
    // Also try to read from localStorage (fallback)
    if (recommendations.length === 0) {
        const savedLocal = localStorage.getItem('quiz_results');
        if (savedLocal) {
            try {
                recommendations = JSON.parse(savedLocal);
            } catch (e) {
                console.error("Error parsing local results:", e);
            }
        }
    }

    // Update sidebar with saved quiz data if available
    updateSidebar();

    if (recommendations && recommendations.length > 0) {
        // Show results
        setTimeout(() => {
            loadingSpinner.classList.add('hidden');
            resultsContainer.classList.remove('hidden');
            resultsContainer.classList.add('fade-in');
            if (startOverBar) startOverBar.classList.remove('hidden');
            renderRecommendations(recommendations);
        }, 800);
    } else {
        // Show error / no results
        setTimeout(() => {
            loadingSpinner.classList.add('hidden');
            if (startOverBar) startOverBar.classList.remove('hidden');
            renderRecommendations([]);
        }, 600);
    }

    // Retry button
    const retryBtn = document.getElementById('retry-button');
    if (retryBtn) {
        retryBtn.addEventListener('click', () => {
            window.location.href = '/quiz';
        });
    }

    function updateSidebar() {
        const quizData = sessionStorage.getItem('quiz_data') || localStorage.getItem('quiz_data');
        if (quizData) {
            try {
                const data = JSON.parse(quizData);
                const useCaseEl = document.getElementById('summary-use-case');
                const performanceEl = document.getElementById('summary-performance');
                const screenSizeEl = document.getElementById('summary-screen-size');
                const portabilityEl = document.getElementById('summary-portability');
                const brandEl = document.getElementById('summary-brand');
                const budgetEl = document.getElementById('summary-budget');

                const labels = {
                    'work': 'Work', 'gaming': 'Gaming', 'content_creation': 'Creative Work', 'general': 'Daily Use',
                    'entry': 'Entry Level', 'medium': 'Balanced', 'high': 'High',
                    '13-14': '13" - 14"', '15-16': '15" - 16"', '17+': '17"+',
                    'low': 'Low'
                };

                if (data.use_case && useCaseEl) useCaseEl.textContent = labels[data.use_case] || data.use_case;
                if (data.performance && performanceEl) performanceEl.textContent = labels[data.performance] || data.performance;
                if (data.screen_size && screenSizeEl) screenSizeEl.textContent = labels[data.screen_size] || data.screen_size;
                if (data.portability && portabilityEl) portabilityEl.textContent = labels[data.portability] || data.portability;
                if (data.brand && brandEl) brandEl.textContent = data.brand;
                if (data.budget && budgetEl) budgetEl.textContent = data.budget;
            } catch (e) {
                console.error("Error updating sidebar:", e);
            }
        }
    }

    function renderRecommendations(laptops) {
        if (!resultsContainer) return;
        resultsContainer.innerHTML = '';

        if (!laptops || laptops.length === 0) {
            resultsContainer.innerHTML = `
                <div class="bg-dark-card rounded-2xl p-10 border border-dark-border text-center flex flex-col items-center gap-4 fade-in">
                    <div class="w-16 h-16 rounded-full bg-dark-surface flex items-center justify-center text-dark-text-subtle">
                        <span class="material-symbols-outlined text-[36px]">search_off</span>
                    </div>
                    <h3 class="font-headline-md text-headline-md text-dark-text">No Laptops Found</h3>
                    <p class="font-body-md text-body-md text-dark-text-muted max-w-md">
                        We couldn't find any matching laptops within your budget range. Try starting over with a higher budget limit.
                    </p>
                    <a href="/quiz" class="px-6 py-2.5 bg-electric-blue text-white rounded-full font-label-md text-label-md font-semibold hover:bg-electric-blue-dark transition-all inline-flex items-center gap-2 mt-2">
                        <span class="material-symbols-outlined text-[16px]">restart_alt</span>
                        Try Again
                    </a>
                </div>
            `;
            return;
        }

        laptops.forEach((laptop, index) => {
            const card = createRecommendationCard(laptop, index);
            card.classList.add(`stagger-${Math.min(index + 1, 3)}`);
            resultsContainer.appendChild(card);
        });
    }

    function createRecommendationCard(laptop, index) {
        const isTop = index === 0;
        const matchScore = laptop.match_score || (98 - index * 3);
        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';
        
        const card = document.createElement('div');
        card.className = `bg-dark-card rounded-2xl p-6 border border-dark-border hover:border-electric-blue/40 transition-all duration-300 ${
            isTop ? 'border-electric-blue/30 shadow-lg shadow-electric-blue/5' : ''
        }`;

        // Build retail offers HTML
        let offersHtml = '';
        if (laptop.shop_offers && laptop.shop_offers.length > 0) {
            offersHtml = `
                <div class="mt-5 pt-5 border-t border-dark-border">
                    <span class="text-[11px] font-bold text-dark-text-subtle uppercase tracking-wider block mb-3 font-label-md">Available At Local Stores</span>
                    <div class="flex flex-col gap-2">
                        ${laptop.shop_offers.map(offer => `
                            <div class="flex justify-between items-center bg-dark-surface p-3 rounded-xl border border-dark-border hover:border-dark-text-muted/20 transition-colors">
                                <span class="font-label-md text-[13px] text-dark-text font-medium">${offer.shop_name}</span>
                                <div class="flex items-center gap-3">
                                    <span class="font-bold text-jod-green text-[14px]">${offer.price_jod} JOD</span>
                                    ${offer.product_url ? `
                                        <a href="${offer.product_url}" target="_blank" class="px-3 py-1.5 bg-electric-blue text-white rounded-full text-[11px] font-semibold hover:bg-electric-blue-dark transition-colors inline-flex items-center gap-1">
                                            View Deal
                                            <span class="material-symbols-outlined text-[12px]">open_in_new</span>
                                        </a>
                                    ` : ''}
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        } else {
            offersHtml = `
                <div class="mt-5 pt-5 border-t border-dark-border text-center text-dark-text-subtle text-[13px]">
                    Price details not available. Contact retailers directly.
                </div>
            `;
        }

        card.innerHTML = `
            <div>
                ${isTop ? `
                    <div class="flex items-center gap-2 mb-5">
                        <div class="w-8 h-8 rounded-full bg-jod-green/15 flex items-center justify-center">
                            <span class="material-symbols-outlined material-filled text-jod-green text-[16px]">bolt</span>
                        </div>
                        <span class="text-[12px] font-bold text-jod-green uppercase tracking-wider font-label-md">Top Pick</span>
                    </div>
                ` : ''}
                
                <div class="flex gap-6 items-start">
                    <div class="w-28 h-28 bg-dark-surface rounded-xl overflow-hidden flex items-center justify-center shrink-0 border border-dark-border">
                        <img src="${imageUrl}" alt="${laptop.model}" class="object-contain max-h-24 max-w-full hover:scale-105 transition-transform duration-300" onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
                    </div>
                    <div class="flex-grow">
                        <div class="flex justify-between items-start">
                            <div>
                                <h3 class="font-headline-md text-[20px] font-bold text-dark-text leading-tight">${laptop.brand} ${laptop.model}</h3>
                                <span class="text-[13px] text-dark-text-muted font-semibold block mt-1">JOD ${laptop.price_jod}</span>
                            </div>
                            <div class="flex flex-col items-center justify-center bg-electric-blue/10 text-electric-blue rounded-full w-14 h-14 border border-electric-blue/20 shrink-0">
                                <span class="font-bold text-[16px]">${matchScore}%</span>
                                <span class="text-[9px] uppercase font-bold tracking-widest text-dark-text-subtle -mt-0.5">Match</span>
                            </div>
                        </div>

                        <!-- Spec List -->
                        <div class="grid grid-cols-2 gap-x-4 gap-y-2 mt-4 bg-dark-surface p-3.5 rounded-xl border border-dark-border">
                            <div class="flex items-center gap-2 text-dark-text-muted text-[13px]">
                                <span class="material-symbols-outlined text-[18px] text-dark-text-subtle">memory</span>
                                <span class="truncate" title="${laptop.cpu || ''}">${laptop.cpu || 'Intel / AMD CPU'}</span>
                            </div>
                            <div class="flex items-center gap-2 text-dark-text-muted text-[13px]">
                                <span class="material-symbols-outlined text-[18px] text-dark-text-subtle">developer_board</span>
                                <span class="truncate" title="${laptop.gpu || ''}">${laptop.gpu || 'Integrated GPU'}</span>
                            </div>
                            <div class="flex items-center gap-2 text-dark-text-muted text-[13px]">
                                <span class="material-symbols-outlined text-[18px] text-dark-text-subtle">ram</span>
                                <span>${laptop.ram || '8GB RAM'}</span>
                            </div>
                            <div class="flex items-center gap-2 text-dark-text-muted text-[13px]">
                                <span class="material-symbols-outlined text-[18px] text-dark-text-subtle">hard_drive</span>
                                <span>${laptop.storage || '256GB'} ${laptop.storage_type || 'SSD'}</span>
                            </div>
                            <div class="flex items-center gap-2 text-dark-text-muted text-[13px] col-span-2">
                                <span class="material-symbols-outlined text-[18px] text-dark-text-subtle">aspect_ratio</span>
                                <span>${laptop.screen_size ? laptop.screen_size + '"' : '15.6"'} Screen</span>
                            </div>
                        </div>

                        <!-- Reasoning -->
                        <div class="bg-dark-surface border border-dark-border rounded-xl p-4 mt-4">
                            <div class="flex items-center gap-2 font-bold text-electric-blue text-[13px] mb-1.5">
                                <span class="material-symbols-outlined text-[16px]">sparkles</span>
                                Why This Laptop
                            </div>
                            <p class="font-body-md text-[13px] text-dark-text-muted leading-relaxed">
                                ${laptop.reasoning || 'Matches your required specifications and budget nicely. High reliability rating in Amman local marketplace.'}
                            </p>
                        </div>
                    </div>
                </div>

                <!-- Shop Offers list -->
                ${offersHtml}
            </div>
        `;
        
        return card;
    }
});
