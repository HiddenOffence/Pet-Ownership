// Get pet data from the server
fetch('/api/pets')
    .then(response => response.json())
    .then(data => {
        // Store pet data globally - keyed by name instead of ID
        window.petData = {};
        data.pets.forEach(pet => {
            window.petData[pet.name] = pet;  // Changed from pet.id to pet.name
        });
        
        // Set up event listeners
        document.getElementById('pet1').addEventListener('change', function() {
            updatePetPreview(this.value, 'preview1');
            checkSelections();
        });

        document.getElementById('pet2').addEventListener('change', function() {
            updatePetPreview(this.value, 'preview2');
            checkSelections();
        });
    })
    .catch(error => {
        console.error('Error fetching pet data:', error);
        // Show error message in preview boxes
        document.getElementById('preview1').innerHTML = '<p>Error loading pet data</p>';
        document.getElementById('preview2').innerHTML = '<p>Error loading pet data</p>';
    });

function updatePetPreview(petName, previewId) {  // Changed parameter name from petId to petName
    const preview = document.getElementById(previewId);
    
    if (!petName) {
        preview.innerHTML = '<p>Select a pet to see details</p>';
        return;
    }
    
    const pet = window.petData[petName];  // Look up by name instead of ID
    if (pet) {
        preview.innerHTML = `
            <h4>${pet.name}</h4>
            <p><strong>Species:</strong> ${pet.species_name || 'Unknown'}</p>
            <p><strong>Lifespan:</strong> ${pet.lifespan || 'Unknown'}</p>
            <p><strong>Setup Cost:</strong> $${pet.cost_setup || 'Unknown'}</p>
            <p><strong>Daily Care:</strong> ${pet.daily_time_min || 'Unknown'} minutes</p>
            <p><strong>Difficulty:</strong> ${pet.difficulty || 'Unknown'}/5</p>
        `;
    } else {
        preview.innerHTML = '<p>Pet information not available</p>';
    }
}

// Enable/disable compare button based on selection
function checkSelections() {
    const pet1 = document.getElementById('pet1').value;
    const pet2 = document.getElementById('pet2').value;
    const compareBtn = document.querySelector('.compare-btn');
}
    

// Initialize button state
document.addEventListener('DOMContentLoaded', function() {
    checkSelections();
});