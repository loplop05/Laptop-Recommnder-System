document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recommend-form');
    const resultsSection = document.getElementById('results-section');
    const container = document.getElementById('recommendations-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const refreshBtn = document.getElementById('refresh-prices-btn');
    const startOverBtn = document.getElementById('start-over-btn');

    // Wizard Logic
    let currentStep = 1;
    const totalSteps = 7;
    const steps = document.querySelectorAll('.step');
    const progressBar = document.getElementById('progress');
    const stepCount = document.getElementById('step-count');
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const submitBtn = document.getElementById('submit-btn');

    // Budget slider live update
    const budgetSlider = document.getElementById('budget');
    const budgetOutput = document.getElementById('budget-output');

    budgetSlider.addEventListener('input', (e) => {
        budgetOutput.textContent = e.target.value;
    });

    // Handle Enter key for navigation
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
                return;
            }

            if (currentStep < totalSteps) {
                e.preventDefault();
                nextBtn.click();
            } else {
                e.preventDefault();
                submitBtn.click();
            }
        }
    });

    updateWizard();

    function updateWizard() {
        console.log('Updating wizard to step:', currentStep);
        steps.forEach(s => s.classList.remove('active'));
        const activeStep = document.querySelector(`.step[data-step="${currentStep}"]`);
        if (activeStep) {
            activeStep.classList.add('active');
        }

        // Update progress bar
        const progressPercent = (currentStep / totalSteps) * 100;
        progressBar.style.width = `${progressPercent}%`;
        stepCount.textContent = `Step ${currentStep} of ${totalSteps}`;

        // Update button visibility
        if (currentStep === 1) {
            prevBtn.classList.add('hidden');
        } else {
            prevBtn.classList.remove('hidden');
        }

        if (currentStep === totalSteps) {
            nextBtn.classList.add('hidden');
            submitBtn.classList.remove('hidden');
        } else {
            nextBtn.classList.remove('hidden');
            submitBtn.classList.add('hidden');
        }

        // Scroll to wizard
        document.getElementById('wizard-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    // Auto-advance on card selection for certain steps
    document.querySelectorAll('.option-card input').forEach(input => {
        input.addEventListener('change', () => {
            // Auto-advance on steps 1, 3, 4, 5, 6 (use case, screen, portability, performance, os)
            if ([1, 3, 4, 5, 6].includes(currentStep)) {
                setTimeout(() => {
                    if (currentStep < totalSteps) {
                        currentStep++;
                        updateWizard();
                    }
                }, 300);
            }
        });
    });

    nextBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Next button clicked. Current step:', currentStep);

        // Validation for step 1: Use Case
        if (currentStep === 1) {
            const useCase = document.querySelector('input[name="use_case"]:checked');
            if (!useCase) {
                alert('Please select a use case.');
                return;
            }
        }

        // Validation for step 2: Budget
        if (currentStep === 2) {
            const budget = parseInt(budgetSlider.value);
            if (budget < 100 || budget > 10000) {
                alert('Please set a valid budget between 100 and 10000 JOD.');
                return;
            }
        }

        if (currentStep < totalSteps) {
            currentStep++;
            updateWizard();
        }
    });

    prevBtn.addEventListener('click', (e) => {
        e.preventDefault();
        console.log('Prev clicked, current step:', currentStep);
        if (currentStep > 1) {
            currentStep--;
            updateWizard();
        }
    });

    // Form Submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Get form values
        const useCase = document.querySelector('input[name="use_case"]:checked').value;
        const budget = parseInt(budgetSlider.value);
        const screenSize = document.querySelector('input[name="screen_size"]:checked').value;
        const portability = document.querySelector('input[name="portability"]:checked').value;
        const performance = document.querySelector('input[name="performance"]:checked').value;
        const osPreference = document.querySelector('input[name="os_preference"]:checked').value;
        const brand = document.querySelector('input[name="brand"]:checked').value;

        // Map OS preference to brand for backend
        let mappedBrand = brand;
        if (brand === 'Any') {
            // If user selected a specific OS, map it
            if (osPreference === 'macos') {
                mappedBrand = 'Apple';
            } else if (osPreference === 'windows') {
                mappedBrand = 'Any'; // Windows is available from all brands
            } else {
                mappedBrand = 'Any';
            }
        }

        const data = {
            budget: budget,
            use_case: useCase,
            performance: performance,
            screen_size: screenSize,
            portability: portability,
            brand: mappedBrand
        };

        console.log('Submitting recommendation request:', data);
        showLoading(true);

        try {
            const response = await fetch('/api/recommend', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                let errMsg = `Server error (${response.status})`;
                try {
                    const ct = response.headers.get('content-type') || '';
                    if (ct.includes('application/json')) {
                        const errorData = await response.json();
                        errMsg = errorData.error || errMsg;
                    } else {
                        errMsg = `${errMsg}: ${response.statusText}`;
                    }
                } catch (_) { /* ignore secondary parse error */ }
                throw new Error(errMsg);
            }

            const result = await response.json();
            displayRecommendations(result.recommendations || [], data);
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            showLoading(false);
        }
    });

    startOverBtn.addEventListener('click', () => {
        // Reset form
        form.reset();
        currentStep = 1;
        updateWizard();
        resultsSection.classList.add('hidden');
        document.getElementById('wizard-container').scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        refreshBtn.textContent = 'Syncing...';
        try {
            const response = await fetch('/api/refresh-prices', { method: 'POST' });
            const result = await response.json();
            alert(result.message);
        } catch (error) {
            alert('Failed to refresh prices');
        } finally {
            refreshBtn.disabled = false;
            refreshBtn.textContent = 'Sync Market Prices';
        }
    });

    function showLoading(show) {
        if (show) {
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }

    function displayRecommendations(recommendations, userPreferences) {
        container.innerHTML = '';

        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p class="no-results">No matching laptops found. Try adjusting your budget or preferences.</p>';
        } else {
            recommendations.forEach((laptop, index) => {
                const card = createLaptopCard(laptop, index + 1, recommendations.length);
                container.appendChild(card);
            });
        }

        resultsSection.classList.remove('hidden');
        resultsSection.scrollIntoView({ behavior: 'smooth' });
    }

    function createLaptopCard(laptop, rank, totalRecommendations) {
        const card = document.createElement('div');
        card.className = 'laptop-card';

        const imageUrl = laptop.image_url || 'https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80';

        // Use actual match score from API, fall back to rank-based
        const matchScore = laptop.match_score || Math.max(70, 100 - (rank - 1) * 10);

        // Storage: handle both old 'storage' and new 'storage_size' fields
        const storageGB = laptop.storage || laptop.storage_size || 0;
        const storageType = laptop.storage_type || 'SSD';

        // Build specs grid
        const specsHtml = `
            <div class="spec-item">CPU: <strong>${laptop.cpu || 'N/A'}</strong></div>
            <div class="spec-item">GPU: <strong>${laptop.gpu || 'N/A'}</strong></div>
            <div class="spec-item">RAM: <strong>${laptop.ram || 'N/A'}GB</strong></div>
            <div class="spec-item">${storageType}: <strong>${storageGB >= 1024 ? (storageGB / 1024) + 'TB' : storageGB + 'GB'}</strong></div>
        `;

        // Build shop offers section
        const shopOffers = laptop.shop_offers || [];
        let shopsHtml = '';
        if (shopOffers.length > 0) {
            const offerCards = shopOffers.map(offer => {
                const mapLink = offer.shop_map_url
                    ? `<a href="${offer.shop_map_url}" target="_blank" class="shop-map-link" title="View on map">📍 Map</a>`
                    : '';
                const phoneLink = offer.shop_phone
                    ? `<a href="tel:${offer.shop_phone}" class="shop-phone-link" title="Call shop">📞 ${offer.shop_phone}</a>`
                    : '';
                const locationText = offer.shop_location
                    ? `<div class="shop-location">${offer.shop_location}</div>`
                    : '';

                return `
                    <div class="shop-offer-card">
                        <div class="shop-offer-header">
                            <span class="shop-name">${offer.shop_name}</span>
                            <span class="shop-price">${offer.price_jod} JOD</span>
                        </div>
                        ${locationText}
                        <div class="shop-actions">
                            <a href="${offer.product_url}" target="_blank" class="shop-visit-btn">Visit Store</a>
                            ${mapLink}
                            ${phoneLink}
                        </div>
                    </div>
                `;
            }).join('');

            shopsHtml = `
                <div class="shop-offers-section">
                    <div class="shop-offers-title">🏪 Available at ${shopOffers.length} shop${shopOffers.length > 1 ? 's' : ''}</div>
                    <div class="shop-offers-list">
                        ${offerCards}
                    </div>
                </div>
            `;
        }

        // Show compare button only if there are multiple recommendations
        const compareBtn = totalRecommendations > 1 ? `<button type="button" class="compare-btn" data-model="${laptop.model}">Compare</button>` : '';

        // Best price from first offer or direct price
        const bestPrice = laptop.price_jod || (shopOffers.length > 0 ? shopOffers[0].price_jod : 0);
        const bestUrl = laptop.purchase_url || (shopOffers.length > 0 ? shopOffers[0].product_url : '#');

        card.innerHTML = `
            <div class="laptop-image-container">
                <img src="${imageUrl}" alt="${laptop.model}" class="laptop-image" onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
            </div>
            <div class="laptop-content">
                <div class="match-score-container">
                    <div class="match-score-label">${matchScore}% Compatibility</div>
                    <div class="match-score-bar-bg">
                        <div class="match-score-bar" style="width: ${matchScore}%;"></div>
                    </div>
                </div>
                <div class="laptop-brand">${laptop.brand}</div>
                <div class="laptop-model">${laptop.model}</div>
                <div class="ai-reasoning">
                    <strong>Why we picked this:</strong>
                    ${laptop.reasoning || 'Highly recommended based on your specific needs and current market value.'}
                </div>
                <div class="laptop-specs">
                    ${specsHtml}
                </div>
                ${shopsHtml}
                <div class="laptop-footer">
                    <div class="laptop-price">${bestPrice} JOD</div>
                    <a href="${bestUrl}" target="_blank" class="buy-btn">Best Deal</a>
                    ${compareBtn}
                </div>
            </div>
        `;

        // Store laptop data for compare functionality
        card.dataset.laptop = JSON.stringify(laptop);

        return card;
    }
});
