document.addEventListener('DOMContentLoaded', function () {
    const portalTime = document.getElementById('portalTime');
    const portalDate = document.getElementById('portalDate');
    if (portalTime && portalDate) {
        const updatePortalClock = function () {
            const now = new Date();
            portalTime.textContent = now.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
            portalDate.textContent = now.toLocaleDateString([], {
                day: '2-digit',
                month: 'short',
                year: 'numeric'
            });
        };
        updatePortalClock();
        window.setInterval(updatePortalClock, 1000);
    }

    const loginElapsed = document.getElementById('loginElapsed');
    if (loginElapsed) {
        const pageOpenedAt = Date.now();
        const updateLoginElapsed = function () {
            const elapsedSeconds = Math.floor((Date.now() - pageOpenedAt) / 1000);
            const minutes = String(Math.floor(elapsedSeconds / 60)).padStart(2, '0');
            const seconds = String(elapsedSeconds % 60).padStart(2, '0');
            loginElapsed.textContent = `${minutes}:${seconds}`;
        };
        updateLoginElapsed();
        window.setInterval(updateLoginElapsed, 1000);
    }

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value.trim();
            const errorBox = document.getElementById('loginError');

            if (!username || !password) {
                errorBox.textContent = 'Please enter both username and password.';
                return;
            }

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const payload = await response.json();

                if (!response.ok || !payload.success) {
                    errorBox.textContent = payload.message || 'Login failed.';
                    return;
                }

                window.location.href = '/dashboard';
            } catch (error) {
                errorBox.textContent = 'Unable to log in right now. Please try again.';
            }
        });
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async function (event) {
            event.preventDefault();
            const fullName = document.getElementById('fullName').value.trim();
            const ageValue = document.getElementById('driverAge').value.trim();
            const phoneValue = document.getElementById('driverPhone').value.trim();
            const username = document.getElementById('newUsername').value.trim();
            const password = document.getElementById('newPassword').value.trim();
            const messageBox = document.getElementById('registerMessage');

            if (!fullName || !username || !password) {
                messageBox.textContent = 'Enter your name, username, and password.';
                return;
            }

            const age = ageValue ? Number(ageValue) : null;
            if (ageValue && (!Number.isFinite(age) || age < 18 || age > 80)) {
                messageBox.textContent = 'Please enter a valid driver age between 18 and 80.';
                return;
            }

            try {
                const response = await fetch('/api/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        full_name: fullName,
                        age,
                        phone: phoneValue,
                        username,
                        password
                    })
                });
                const payload = await response.json();
                if (!response.ok || !payload.success) {
                    messageBox.textContent = payload.message || 'Unable to create account.';
                    return;
                }
                window.location.href = '/dashboard';
            } catch (error) {
                messageBox.textContent = 'Unable to create account right now.';
            }
        });
    }

    const backBtn = document.getElementById('backBtn');
    if (backBtn) {
        backBtn.addEventListener('click', function () {
            if (window.history.length > 1) {
                window.history.back();
            } else {
                window.location.href = '/';
            }
        });
    }

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async function () {
            await fetch('/api/logout', { method: 'POST' });
            window.location.href = '/login';
        });
    }

    const searchHospitalBtn = document.getElementById('searchHospitalBtn');
    const useLocationBtn = document.getElementById('useLocationBtn');
    const addressInput = document.getElementById('addressInput');
    const locationStatus = document.getElementById('locationStatus');
    const searchError = document.getElementById('searchError');
    const hospitalResults = document.getElementById('hospitalResults');
    const recommendedHospital = document.getElementById('recommendedHospital');
    const startNavigationBtn = document.getElementById('startNavigationBtn');
    const finishBtn = document.getElementById('finishBtn');
    const exitMapBtn = document.getElementById('exitMapBtn');
    const newEmergencyBtn = document.getElementById('newEmergencyBtn');

    let map;
    let startMarker;
    let hospitalMarkers = [];
    let routeLine = null;
    let currentCoords = null;
    let currentHospital = null;
    let currentHospitals = [];
    let searchTimer = null;
    let activeSearchAddress = '';

    const createMap = () => {
        if (map || !document.getElementById('map') || typeof L === 'undefined') {
            return;
        }
        map = L.map('map').setView([11.1271, 78.6569], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);
    };

    createMap();

    const clearMapMarkers = () => {
        hospitalMarkers.forEach(marker => map.removeLayer(marker));
        hospitalMarkers = [];

        if (routeLine) {
            map.removeLayer(routeLine);
            routeLine = null;
        }
    };

    const updateMap = (lat, lng, hospitals, bestHospital, routeCoordinates = null) => {
        map.setView([lat, lng], 12);

        if (startMarker) {
            map.removeLayer(startMarker);
        }
        startMarker = L.marker([lat, lng]).addTo(map).bindPopup('Accident / emergency location').openPopup();

        clearMapMarkers();

        hospitals.forEach((hospital) => {
            const hospitalMarker = L.marker([hospital.latitude, hospital.longitude]).addTo(map);
            hospitalMarker.bindPopup(`${hospital.name}<br>${hospital.beds_available} beds available`);
            hospitalMarkers.push(hospitalMarker);
        });

        if (bestHospital) {
            const bestMarker = L.marker([bestHospital.latitude, bestHospital.longitude]).addTo(map);
            bestMarker.bindPopup(`Recommended: ${bestHospital.name}`);
            bestMarker.setIcon(L.divIcon({
                html: '<div style="background:#1e8e3e;border-radius:50%;width:18px;height:18px;border:3px solid white;"></div>',
                className: '',
                iconSize: [18, 18]
            }));
            hospitalMarkers.push(bestMarker);

            routeLine = L.polyline(routeCoordinates || [
                [lat, lng],
                [bestHospital.latitude, bestHospital.longitude]
            ], { color: '#d32f2f', weight: 5 }).addTo(map);

            map.fitBounds([
                ...(routeCoordinates || [
                    [lat, lng],
                    [bestHospital.latitude, bestHospital.longitude]
                ])
            ]);
        }
    };

    const renderResults = (hospitals, bestHospital) => {
        if (!hospitals || hospitals.length === 0) {
            hospitalResults.innerHTML = '<p>No hospitals found within range.</p>';
            recommendedHospital.textContent = 'No hospital found for this emergency location.';
            startNavigationBtn.disabled = true;
            return;
        }

        if (!bestHospital) {
            hospitalResults.innerHTML = hospitals.map((hospital) => `
                <div class="hospital-card">
                    <h4>${hospital.name}</h4>
                    <p><strong>Distance:</strong> ${hospital.distance_km} km</p>
                    <p><strong>Available Beds:</strong> ${hospital.beds_available}</p>
                    <p><strong>Status:</strong> No emergency beds available</p>
                </div>
            `).join('');
            recommendedHospital.textContent = 'No nearby hospital currently has available beds.';
            startNavigationBtn.disabled = true;
            return;
        }

        hospitalResults.innerHTML = `<p class="results-count">Showing ${hospitals.length} nearby hospitals with available beds.</p>` + hospitals.map((hospital) => {
            const active = bestHospital && hospital.id === bestHospital.id ? 'highlight' : '';
            return `
                <div class="hospital-card ${active}" data-hospital-id="${hospital.id}">
                    <h4>${hospital.name}</h4>
                    <p><strong>Distance:</strong> ${hospital.distance_km} km</p>
                    <p><strong>Travel Time:</strong> ${hospital.travel_time_minutes} min</p>
                    <p><strong>Traffic:</strong> ${hospital.traffic_level}</p>
                    <p><strong>Available Beds:</strong> ${hospital.beds_available}</p>
                    <button type="button" class="go-btn" data-hospital-id="${hospital.id}">Go</button>
                </div>
            `;
        }).join('');

        if (bestHospital) {
            recommendedHospital.innerHTML = `
                <strong>Recommended Hospital:</strong> ${bestHospital.name}<br>
                ${bestHospital.distance_km} km away, ${bestHospital.travel_time_minutes} minutes estimated travel time,<br>
                ${bestHospital.beds_available} beds available.
            `;
            startNavigationBtn.disabled = false;
        }
    };

    const selectHospital = async (hospital) => {
        if (!currentCoords || !hospital) {
            return;
        }

        currentHospital = hospital;
        document.body.classList.add('route-map-active');
        window.setTimeout(function () {
            map.invalidateSize();
        }, 150);
        await loadRecommendedRoute(currentCoords, hospital, currentHospitals);
        recommendedHospital.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    const loadRecommendedRoute = async (coordinates, bestHospital, hospitals) => {
        if (!bestHospital) {
            updateMap(coordinates.latitude, coordinates.longitude, hospitals, null);
            return;
        }

        try {
            const response = await fetch('/api/hospitals/route', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_lat: coordinates.latitude,
                    start_lng: coordinates.longitude,
                    hospital_lat: bestHospital.latitude,
                    hospital_lng: bestHospital.longitude
                })
            });
            const payload = await response.json();

            if (!response.ok || !payload.success) {
                searchError.textContent = payload.message || 'Road route unavailable. Showing a direct route instead.';
                updateMap(coordinates.latitude, coordinates.longitude, hospitals, bestHospital);
                return;
            }

            const route = payload.route;
            bestHospital.distance_km = route.distance_km;
            bestHospital.travel_time_minutes = route.travel_time_minutes;
            bestHospital.traffic_level = route.traffic_level;
            renderResults(hospitals, bestHospital);
            updateMap(coordinates.latitude, coordinates.longitude, hospitals, bestHospital, route.polyline);
        } catch (error) {
            searchError.textContent = 'Road service unavailable. Showing a direct route instead.';
            updateMap(coordinates.latitude, coordinates.longitude, hospitals, bestHospital);
        }
    };

    const handleSearch = async () => {
        const address = addressInput.value.trim();
        if (!address) {
            searchError.textContent = 'Please enter an emergency location.';
            return;
        }

        activeSearchAddress = address;

        searchHospitalBtn.disabled = true;
        searchHospitalBtn.textContent = 'Finding hospital and route...';
        searchError.textContent = '';

        const coordinates = await getCoordinatesFromAddress(address);
        if (!coordinates) {
            searchHospitalBtn.disabled = false;
            searchHospitalBtn.textContent = 'Find 6-7 Nearby Hospitals & Route';
            return;
        }

        currentCoords = coordinates;
        locationStatus.textContent = `Location: ${address} (${coordinates.latitude.toFixed(4)}, ${coordinates.longitude.toFixed(4)})`;
        searchError.textContent = '';

        try {
            const response = await fetch('/api/hospitals/nearest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    address,
                    latitude: coordinates.latitude,
                    longitude: coordinates.longitude
                })
            });

            const payload = await response.json();
            if (!response.ok || !payload.success) {
                searchError.textContent = payload.message || 'Unable to find nearby hospitals.';
                return;
            }

            const bestHospital = payload.recommended_hospital;
            currentHospitals = payload.hospitals;
            renderResults(payload.hospitals, bestHospital);
            updateMap(coordinates.latitude, coordinates.longitude, payload.hospitals, bestHospital);
            currentHospital = bestHospital;
            await loadRecommendedRoute(coordinates, bestHospital, payload.hospitals);
        } catch (error) {
            searchError.textContent = 'Error searching hospitals. Please try again.';
        } finally {
            searchHospitalBtn.disabled = false;
            searchHospitalBtn.textContent = 'Find 6-7 Nearby Hospitals & Route';
        }
    };

    const getCoordinatesFromAddress = async (address) => {
        try {
            const response = await fetch('/api/locations/geocode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address })
            });
            const payload = await response.json();

            if (!response.ok || !payload.success) {
                searchError.textContent = payload.message || 'Unable to locate this address.';
                return null;
            }

            return {
                latitude: parseFloat(payload.location.latitude),
                longitude: parseFloat(payload.location.longitude)
            };
        } catch (error) {
            searchError.textContent = 'Location lookup error. Please check the address.';
            return null;
        }
    };

    if (searchHospitalBtn) {
        searchHospitalBtn.addEventListener('click', handleSearch);
    }

    if (addressInput) {
        addressInput.addEventListener('input', function () {
            window.clearTimeout(searchTimer);
            const address = addressInput.value.trim();
            if (address.length < 3) {
                return;
            }
            searchTimer = window.setTimeout(function () {
                if (addressInput.value.trim() === address && activeSearchAddress !== address) {
                    handleSearch();
                }
            }, 900);
        });
        addressInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter') {
                event.preventDefault();
                window.clearTimeout(searchTimer);
                handleSearch();
            }
        });
    }

    if (hospitalResults) {
        hospitalResults.addEventListener('click', function (event) {
            const goButton = event.target.closest('.go-btn');
            if (!goButton) {
                return;
            }
            const hospital = currentHospitals.find((item) => String(item.id) === goButton.dataset.hospitalId);
            selectHospital(hospital);
        });
    }

    if (useLocationBtn) {
        useLocationBtn.addEventListener('click', function () {
            if (!navigator.geolocation) {
                searchError.textContent = 'This browser does not support geolocation.';
                return;
            }

            navigator.geolocation.getCurrentPosition(async function (position) {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                const reverseUrl = `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lng}`;

                try {
                    const response = await fetch(reverseUrl, { headers: { 'User-Agent': 'EmergencyAmbulanceRouteOptimizer/1.0' } });
                    const data = await response.json();
                    const placeName = data.display_name || 'Current location';
                    addressInput.value = placeName;
                    locationStatus.textContent = `Current location detected (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
                    searchError.textContent = '';

                    const responseHospitals = await fetch('/api/hospitals/nearest', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ address: placeName, latitude: lat, longitude: lng })
                    });
                    const payload = await responseHospitals.json();

                    if (!responseHospitals.ok || !payload.success) {
                        searchError.textContent = payload.message || 'Unable to find nearby hospitals.';
                        return;
                    }

                    const bestHospital = payload.recommended_hospital;
                    currentHospitals = payload.hospitals;
                    renderResults(payload.hospitals, bestHospital);
                    updateMap(lat, lng, payload.hospitals, bestHospital);
                    currentHospital = bestHospital;
                    await loadRecommendedRoute({ latitude: lat, longitude: lng }, bestHospital, payload.hospitals);
                } catch (error) {
                    searchError.textContent = 'Unable to identify your current location.';
                }
            }, function () {
                searchError.textContent = 'Location permission was denied. Please enter an address manually.';
            });
        });
    }

    if (startNavigationBtn) {
        startNavigationBtn.addEventListener('click', async function () {
            if (!currentCoords || !currentHospital) {
                searchError.textContent = 'Select an emergency location and hospital before starting navigation.';
                return;
            }

            try {
                const response = await fetch('/api/hospitals/route', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start_lat: currentCoords.latitude,
                        start_lng: currentCoords.longitude,
                        hospital_lat: currentHospital.latitude,
                        hospital_lng: currentHospital.longitude
                    })
                });
                const payload = await response.json();

                if (!response.ok || !payload.success) {
                    searchError.textContent = payload.message || 'Route information unavailable.';
                    return;
                }

                const route = payload.route;
                searchError.textContent = `Route ready: ${route.distance_km} km, ${route.travel_time_minutes} minutes, traffic: ${route.traffic_level}`;
                finishBtn.disabled = false;
                window.alert(`Navigation started to ${currentHospital.name}. Estimated travel time: ${route.travel_time_minutes} minutes.`);
            } catch (error) {
                searchError.textContent = 'Unable to start navigation.';
            }
        });
    }

    if (finishBtn) {
        finishBtn.addEventListener('click', async function () {
            try {
                const response = await fetch('/api/emergency/finish', { method: 'POST' });
                const payload = await response.json();
                if (!response.ok || !payload.success) {
                    searchError.textContent = payload.message || 'Unable to finish emergency.';
                    return;
                }
                searchError.textContent = `Emergency completed at ${currentHospital ? currentHospital.name : 'the receiving hospital'}.`;
                finishBtn.disabled = true;
                startNavigationBtn.disabled = true;
            } catch (error) {
                searchError.textContent = 'Unable to finish emergency.';
            }
        });
    }

    if (exitMapBtn) {
        exitMapBtn.addEventListener('click', function () {
            document.body.classList.remove('route-map-active');
        });
    }

    if (newEmergencyBtn) {
        newEmergencyBtn.addEventListener('click', function () {
            addressInput.value = '';
            activeSearchAddress = '';
            window.clearTimeout(searchTimer);
            locationStatus.textContent = 'No location selected yet.';
            searchError.textContent = '';
            hospitalResults.innerHTML = '';
            currentHospitals = [];
            recommendedHospital.textContent = 'No hospital selected yet.';
            startNavigationBtn.disabled = true;
            finishBtn.disabled = true;
            if (map) {
                map.setView([11.1271, 78.6569], 7);
            }
        });
    }
});
