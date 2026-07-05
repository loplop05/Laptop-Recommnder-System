document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('recommend-form');
    const resultsSection = document.getElementById('results-section');
    const container = document.getElementById('recommendations-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const refreshBtn = document.getElementById('refresh-prices-btn');

    // Wizard Logic
    let currentStep = 1;
    const totalSteps = 4;
    const steps = document.querySelectorAll('.step');
    const progressBar = document.getElementById('progress');
    const nextBtn = document.getElementById('next-btn');
    const prevBtn = document.getElementById('prev-btn');
    const submitBtn = document.getElementById('submit-btn');

    function updateWizard() {
        console.log('Updating wizard to step:', currentStep);
        steps.forEach(s => s.classList.remove('active'));
        const activeStep = document.querySelector(`.step[data-step="${currentStep}"]`);
        if (activeStep) {
            activeStep.classList.add('active');
        }
        
        progressBar.style.width = `${(currentStep / totalSteps) * 100}%`;

        // Always show navigation buttons clearly
        prevBtn.style.display = currentStep === 1 ? 'none' : 'block';
        
        if (currentStep === totalSteps) {
            nextBtn.style.display = 'none';
            submitBtn.style.display = 'block';
        } else {
            nextBtn.style.display = 'block';
            submitBtn.style.display = 'none';
        }
    }

    // Auto-advance when an option is clicked in step 1 and 3
    document.querySelectorAll('.option-card input').forEach(input => {
        input.addEventListener('change', () => {
            console.log('Option selected:', input.value);
            // Delay slightly for visual feedback of selection
            if (currentStep === 1 || currentStep === 3) {
                setTimeout(() => {
                    if (currentStep < totalSteps) {
                        currentStep++;
                        updateWizard();
                    }
                }, 400);
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
            console.log('Step 1 validated:', useCase.value);
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
                headers: { 'Content-Type': 'application/json' },
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
        
        card.innerHTML = `
            <img src="${imageUrl}" alt="${laptop.model}" class="laptop-image" onerror="this.src='https://images.unsplash.com/photo-1496181133206-80ce9b88a853?w=500&q=80'">
            <div class="laptop-content">
                <div class="laptop-brand">${laptop.brand}</div>
                <div class="laptop-model">${laptop.model}</div>
                <div class="ai-reasoning">
                    <strong>AI Advice:</strong> ${laptop.reasoning || 'Highly recommended based on your specific needs and current market value.'}
                </div>
                <div class="laptop-specs">
                    <div class="spec-item">CPU: <strong>${laptop.cpu}</strong></div>
                    <div class="spec-item">GPU: <strong>${laptop.gpu}</strong></div>
                    <div class="spec-item">RAM: <strong>${laptop.ram}GB</strong></div>
                    <div class="spec-item">SSD: <strong>${laptop.storage}GB</strong></div>
                    <div class="spec-item">Screen: <strong>${laptop.screen_size}"</strong></div>
                </div>
                <div class="laptop-footer">
                    <div class="laptop-price">${laptop.price_jod} JOD</div>
                    <a href="${laptop.purchase_url}" target="_blank" class="buy-btn">View Store</a>
                </div>
            </div>
        `;
        
        return card;
    }
});
