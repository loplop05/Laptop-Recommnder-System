document.addEventListener('DOMContentLoaded', () => {
    const container = document.getElementById('recommendations-container');
    
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
    
    
    renderRecommendations(recommendations);

    function renderRecommendations(laptops) {
        if (!container) return;
        container.innerHTML = '';

        if (!laptops || laptops.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-12 glass-card rounded-2xl border-white/5">
                    <span class="material-symbols-outlined text-[64px] text-outline mb-4">search_off</span>
                    <h3 class="font-headline-md text-headline-md text-on-surface mb-2">No Laptops Found</h3>
                    <p class="font-body-md text-body-md text-on-surface-variant max-w-md mx-auto">
                        We couldn't find any matching laptops within your budget range. Try starting over with a higher budget limit.
                    </p>
                </div>
            `;
            return;
        }

        laptops.forEach((laptop, index) => {
            const card = createRecommendationCard(laptop, index);
            container.appendChild(card);
        });
    }

    function createRecommendationCard(laptop, index) {
        const isTop = index === 0;
        const matchScore = laptop.match_score || (98 - index * 3);
        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';
        
        const card = document.createElement('div');
        card.className = `relative glass-card rounded-2xl p-6 flex flex-col justify-between border border-white/10 hover:border-electric-blue/30 transition-all duration-300 shadow-xl ${
            isTop ? 'ring-2 ring-electric-blue/40 shadow-electric-blue/5' : ''
        }`;

        // Build retail offers HTML
        let offersHtml = '';
        if (laptop.shop_offers && laptop.shop_offers.length > 0) {
            offersHtml = `
                <div class="mt-4 pt-4 border-t border-white/5">
                    <span class="text-[11px] font-bold text-outline uppercase tracking-wider block mb-2 font-headline-md">Available At Local Stores</span>
                    <div class="flex flex-col gap-2">
                        ${laptop.shop_offers.map(offer => `
                            <div class="flex justify-between items-center bg-surface-container-lowest p-2 rounded-lg border border-white/5 hover:border-white/10 transition-colors">
                                <span class="font-label-sm text-[13px] text-on-surface-variant font-medium">${offer.shop_name}</span>
                                <div class="flex items-center gap-3">
                                    <span class="font-bold text-jod-green text-[14px]">${offer.price_jod} JOD</span>
                                    ${offer.product_url ? `
                                        <a href="${offer.product_url}" target="_blank" class="px-3 py-1 bg-electric-blue text-white rounded text-[11px] font-bold hover:bg-blue-600 transition-colors inline-flex items-center gap-1">
                                            Go to Shop
                                            <span class="material-symbols-outlined text-[10px]">open_in_new</span>
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
                <div class="mt-4 pt-4 border-t border-white/5 text-center text-outline text-[13px]">
                    Price details not available. Contact retailers directly.
                </div>
            `;
        }

        card.innerHTML = `
            <div>
                ${isTop ? `
                    <div class="absolute -top-3 left-6 px-4 py-1 rounded-full bg-gradient-to-r from-electric-blue to-blue-600 text-white font-bold text-[11px] uppercase tracking-wider shadow-lg shadow-blue-500/20">
                        Top Recommendation
                    </div>
                ` : ''}
                
                <div class="w-full h-44 bg-surface-container rounded-xl overflow-hidden flex items-center justify-center relative mb-6 border border-white/5">
                    <img src="${imageUrl}" alt="${laptop.model}" class="object-contain max-h-36 max-w-full hover:scale-105 transition-transform duration-300" onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
                </div>

                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="font-headline-md text-[18px] font-bold text-on-surface leading-tight">${laptop.brand} ${laptop.model}</h3>
                        <span class="text-[12px] text-outline font-bold uppercase tracking-wider block mt-1">JOD ${laptop.price_jod}</span>
                    </div>
                    <div class="flex flex-col items-center justify-center bg-electric-blue/15 text-electric-blue rounded-full w-14 h-14 border border-electric-blue/30 shrink-0">
                        <span class="font-bold text-[16px]">${matchScore}%</span>
                        <span class="text-[9px] uppercase font-bold tracking-widest text-outline -mt-1">Match</span>
                    </div>
                </div>

                <!-- Spec List -->
                <div class="grid grid-cols-2 gap-x-4 gap-y-2 mb-6 bg-surface-container-low p-4 rounded-xl border border-white/5">
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">memory</span>
                        <span class="truncate" title="${laptop.cpu || ''}">${laptop.cpu || 'Intel / AMD CPU'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">developer_board</span>
                        <span class="truncate" title="${laptop.gpu || ''}">${laptop.gpu || 'Integrated GPU'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">ram</span>
                        <span>${laptop.ram || '8GB RAM'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px]">
                        <span class="material-symbols-outlined text-[18px] text-outline">hard_drive</span>
                        <span>${laptop.storage || '256GB'} ${laptop.storage_type || 'SSD'}</span>
                    </div>
                    <div class="flex items-center gap-2 text-on-surface-variant text-[13px] col-span-2">
                        <span class="material-symbols-outlined text-[18px] text-outline">aspect_ratio</span>
                        <span>${laptop.screen_size ? laptop.screen_size + '"' : '15.6"'} Screen</span>
                    </div>
                </div>

                <!-- AI reasoning -->
                <div class="bg-surface-container-highest/30 border border-white/5 rounded-xl p-4 mb-4">
                    <div class="flex items-center gap-2 font-bold text-headline-sm text-electric-blue text-[13px] mb-2">
                        <span class="material-symbols-outlined text-[16px]">sparkles</span>
                        AI Reasoning
                    </div>
                    <p class="font-body-md text-[13px] text-on-surface-variant leading-relaxed">
                        ${laptop.reasoning || 'Matches your required specifications and budget nicely. High reliability rating in Amman local marketplace.'}
                    </p>
                </div>
            </div>

            <!-- Shop Offers list -->
            ${offersHtml}
        `;
        
        return card;
    }
});
