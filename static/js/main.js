document.addEventListener('DOMContentLoaded', () => {
    fetchRecommendations();
    
    // Auto-suggest logic
    const searchInput = document.getElementById('search-input');
    const suggestBox = document.getElementById('suggestions-box');
    
    if (searchInput && suggestBox) {
        let debounceTimer;
        
        searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);
            const query = e.target.value.trim();
            
            if (query.length < 2) {
                suggestBox.style.display = 'none';
                return;
            }
            
            debounceTimer = setTimeout(() => {
                fetch(`/search_suggest?q=${encodeURIComponent(query)}`)
                    .then(r => r.json())
                    .then(data => {
                        if (data.length > 0) {
                            suggestBox.innerHTML = '';
                            data.forEach(item => {
                                const a = document.createElement('a');
                                a.href = `/product/${item.id}`;
                                a.className = 'suggestion-item';
                                a.innerHTML = `
                                    <img src="${item.image_url}" alt="">
                                    <div>
                                        <div style="font-weight: 500">${item.name}</div>
                                        <div style="font-size: 0.8rem; color: #565959">in ${item.category}</div>
                                    </div>
                                `;
                                suggestBox.appendChild(a);
                            });
                            suggestBox.style.display = 'block';
                        } else {
                            suggestBox.style.display = 'none';
                        }
                    });
            }, 300);
        });
        
        // Hide on click outside
        document.addEventListener('click', (e) => {
            if (!searchInput.contains(e.target) && !suggestBox.contains(e.target)) {
                suggestBox.style.display = 'none';
            }
        });
    }
});

function fetchRecommendations() {
    const container = document.getElementById('recommendation-container');
    const loading = document.getElementById('recommendation-loading');
    
    if(!container) return; // Cart/Checkout might not have it
    
    container.innerHTML = '';
    if(loading) loading.style.display = 'block';

    fetch('/recommend')
        .then(response => response.json())
        .then(data => {
            if(loading) loading.style.display = 'none';
            renderProductsRail(data.recommendations, container, "Visit a product to see recommendations!");
        })
        .catch(error => {
            console.error('Error:', error);
            if(loading) loading.style.display = 'none';
        });
}

// Specialized renderer for the horizontal rails matching V3 styles
function renderProductsRail(products, container, emptyMessage) {
    container.innerHTML = ''; 

    if (!products || products.length === 0) {
        if(emptyMessage) {
            container.innerHTML = `<p style="color: #565959; text-align: center; width: 100%;">${emptyMessage}</p>`;
        }
        return;
    }

    products.forEach(p => {
        const finalPrice = p.price - (p.price * ((p.discount || 0) / 100));
        
        const card = document.createElement('div');
        card.className = 'product-card';
        card.onclick = () => window.location.href = `/product/${p.id}`;

        let discountBadge = '';
        if (p.discount && p.discount > 0) {
            discountBadge = `<div class="badge-discount">-${p.discount}%</div>`;
        }

        let oldPrice = '';
        if (p.discount && p.discount > 0) {
            oldPrice = `<span class="product-price-old">$${p.price.toFixed(2)}</span>`;
        }

        card.innerHTML = `
            ${discountBadge}
            <div class="product-image">
                <img src="${p.image_url}" alt="${p.name}">
            </div>
            <div class="product-details">
                <span class="product-category">${p.category}</span>
                <h3 class="product-name" style="font-size: 0.9rem;">${p.name}</h3>
                <div class="rating-stars" style="font-size: 0.8rem;">★★★★☆</div>
                <div class="product-price" style="font-size: 1.1rem;">
                    $${finalPrice.toFixed(2)}
                    ${oldPrice}
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}
