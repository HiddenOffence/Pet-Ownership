// Enhanced interacts - DeepSeek
document.addEventListener('DOMContentLoaded', function() {
    // Half-star hover effect
    const stars = document.querySelectorAll('.star-rating label');
    stars.forEach((star, index) => {
        star.addEventListener('mouseover', () => {
            // Highlight all stars up to the hovered one
            for (let i = stars.length - 1; i >= index; i--) {
                stars[i].style.color = '#ffc107';
            }
        });
        
        star.addEventListener('mouseout', () => {
            // Reset to default state
            const checked = document.querySelector('.star-rating input:checked');
            stars.forEach(s => {
                s.style.color = checked && s.htmlFor <= checked.value ? '#ffc107' : '#ccc';
            });
        });
    });
    
    // Preserve state after hover
    document.querySelectorAll('.star-rating input').forEach(input => {
        input.addEventListener('change', function() {
            const labels = document.querySelectorAll('.star-rating label');
            labels.forEach(label => {
                label.style.color = label.htmlFor <= this.value ? '#ffc107' : '#ccc';
            });
        });
    });
});