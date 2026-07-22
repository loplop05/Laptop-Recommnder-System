document.addEventListener('DOMContentLoaded', () => {
    const resultsContainer = document.getElementById('results-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const startOverBar = document.getElementById('start-over-bar');

    // Retrieve recommendation data from sessionStorage
    const savedResults = sessionStorage.getItem('quiz_results');
    let recommendations = [];
    
    if (savedResults) {
        try {
            recommendations = JSON.parse(savedResults);
        } catch (e) {
            console.error("Error parsing results:", e);
        }
    }

    if (!recommendations || recommendations.length === 0) {
        window.location.href = '/quiz';
        return;
    }

    // Hide spinner and show results
    loadingSpinner.classList.add('hidden');
    resultsContainer.classList.remove('hidden');
    if (startOverBar) startOverBar.classList.remove('hidden');

    // Render recommendations
    recommendations.forEach((laptop, index) => {
        const laptopCard = createLaptopCard(laptop, index);
        resultsContainer.appendChild(laptopCard);
    });

    function createLaptopCard(laptop, index) {
        const section = document.createElement('section');
        section.className = `fade-in grid grid-cols-1 lg:grid-cols-2 gap-gutter mb-stack-lg p-stack-md rounded-2xl glass-panel`;
        section.style.animationDelay = `${index * 0.1}s`;

        const matchScore = laptop.match_score || (98 - index * 3);
        const imageUrl = laptop.image_url || 'https://lh3.googleusercontent.com/aida-public/AB6AXuDqvY2q_2PHR8Ccb8Xxq9QxC9iI4pXmbCDr-z00J_HxqVUspbMx2dWnzMcKWFqd9Lfsojk-t0iZlOqqmzgDSnDBbf7TfFFvb880b0I46GAvsZUeqPXh1S3Z4dGgCcUQCuWA4JifRFpaEJVBST6tmMUQHUKwRtkZkm9Mm16jO73Hroma_7opDcWMXyPGLweVXOuXELZNQTfUtFy0IaMb706OcfSgM5xXXl989ppCwIDcjnHNqSuOYbDOiA';
        
        const offers = laptop.shop_offers || [];

        section.innerHTML = `
            <div class="relative group aspect-square lg:aspect-video rounded-xl overflow-hidden bg-surface-container-low flex items-center justify-center p-8 border border-white/5">
                <img class="w-full h-full object-contain transform group-hover:scale-105 transition-transform duration-700" 
                     src="${imageUrl}" 
                     alt="${laptop.brand} ${laptop.model}"
                     onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
                <div class="absolute top-4 left-4">
                    <span class="bg-electric-blue/20 text-electric-blue px-3 py-1 rounded-full text-label-sm border border-electric-blue/30">
                        ${index === 0 ? 'Top Rated Choice' : 'Great Match'}
                    </span>
                </div>
            </div>
            <div class="flex flex-col justify-center">
                <div class="flex justify-between items-start mb-2">
                    <h1 class="font-headline-lg text-headline-lg-mobile md:text-headline-lg text-on-surface font-bold">${laptop.brand} ${laptop.model}</h1>
                    <div class="flex flex-col items-end">
                        <span class="text-electric-blue font-bold text-xl">${matchScore}%</span>
                        <span class="text-on-surface-variant text-[10px] uppercase tracking-tighter">Match Score</span>
                    </div>
                </div>
                <p class="text-on-surface-variant font-body-lg mb-stack-md">
                    ${laptop.cpu || 'Processor'} | ${laptop.ram || '8GB'} RAM | ${laptop.storage || '256GB'} | ${laptop.gpu || 'Graphics'} | ${laptop.screen_size || '15.6'}"
                </p>
                
                <div class="mb-stack-lg">
                    <div class="text-label-sm text-on-surface-variant mb-1">Current Best Price</div>
                    <div class="flex items-baseline gap-2">
                        <span class="font-display-lg text-display-lg text-electric-blue">${laptop.price_jod}</span>
                        <span class="font-headline-md text-headline-md text-on-surface-variant">JOD</span>
                    </div>
                </div>

                <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-stack-lg">
                    ${offers.length > 0 ? offers.map(offer => `
                        <div class="p-4 rounded-xl border border-white/10 bg-white/5 flex justify-between items-center">
                            <div>
                                <p class="text-on-surface font-semibold text-sm">${offer.shop_name}</p>
                                <p class="text-electric-blue font-bold">${offer.price_jod} JOD</p>
                            </div>
                            <a href="${offer.product_url || '#'}" target="_blank" class="bg-primary-container text-on-primary-container px-4 py-2 rounded-lg text-xs font-bold hover:brightness-110 transition-all">
                                View Deal
                            </a>
                        </div>
                    `).join('') : `
                        <div class="p-4 rounded-xl border border-white/10 bg-white/5 col-span-2 text-center text-on-surface-variant text-sm italic">
                            No local offers found at this time.
                        </div>
                    `}
                </div>

                <div class="flex flex-wrap gap-stack-md">
                    <button class="border border-white/10 text-on-surface px-6 py-3 rounded-xl font-label-md flex items-center gap-2 hover:bg-white/5 active:scale-95 transition-all">
                        <span class="material-symbols-outlined text-[18px]">favorite</span> Save to Wishlist
                    </button>
                    <button class="bg-white/5 text-on-surface-variant px-6 py-3 rounded-xl font-label-md flex items-center gap-2 hover:bg-white/10 transition-all">
                        <span class="material-symbols-outlined text-[18px]">share</span> Share
                    </button>
                </div>
            </div>
        `;

        return section;
    }
});
