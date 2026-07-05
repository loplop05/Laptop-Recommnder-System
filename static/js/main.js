document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recommend-form');
    const resultsSection = document.getElementById('results-section');
    const container = document.getElementById('recommendations-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const refreshBtn = document.getElementById('refresh-prices-btn');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(form);
        const data = {
            budget: parseInt(formData.get('budget')),
            use_case: formData.get('use_case'),
            performance: formData.get('performance'),
            screen_size: formData.get('screen_size'),
            portability: formData.get('portability'),
            brand: formData.get('brand')
        };

        showLoading(true);
        
        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to get recommendations');
            }

            const result = await response.json();
            displayRecommendations(result.recommendations || []);
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            showLoading(false);
        }
    });

    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        refreshBtn.textContent = 'Refreshing...';
        
        try {
            const response = await fetch('/api/refresh-prices', { method: 'POST' });
            const result = await response.json();
            alert(result.message);
        } catch (error) {
            alert('Failed to refresh prices');
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.textContent = 'Refresh Prices';
        }
    });

    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }

    function displayRecommendations(recommendations) {
        container.innerHTML = '';
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="no-results">No matching laptops found. Try adjusting your budget or preferences.</p>';
        } else {
            recommendations.forEach(laptop => {
                const card = createLaptopCard(laptop);
                container.appendChild(card);
            });
        }
        
        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function createLaptopCard(laptop) {
        const card = document.createElement('div');
        card.className = 'laptop-card';
        
        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';
        const recommendedBy = laptop.recommended_by ? laptop.recommended_by.join(', ') : 'ML Pipeline';
        
        card.innerHTML = `
            <img src="${imageUrl}" alt="${laptop.model}" class="laptop-image" onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
            <div class="laptop-content">
                <div class="laptop-brand">${laptop.brand}</div>
                <div class="laptop-model">${laptop.model}</div>
                <div class="recommended-badge">Recommended by: ${recommendedBy}</div>
                <div class="laptop-specs">
                    <div class="spec-item"><span class="spec-label">CPU:</span> ${laptop.cpu}</div>
                    <div class="spec-item"><span class="spec-label">GPU:</span> ${laptop.gpu}</div>
                    <div class="spec-item"><span class="spec-label">RAM:</span> ${laptop.ram}GB</div>
                    <div class="spec-item"><span class="spec-label">Storage:</span> ${laptop.storage}GB</div>
                    <div class="spec-item"><span class="spec-label">Screen:</span> ${laptop.screen_size}"</div>
                </div>
                <div class="laptop-price">${laptop.price_jod} JOD</div>
                <a href="${laptop.purchase_url}" target="_blank" class="buy-btn">View Details</a>
            </div>
        `;
        
        return card;
    }
});
