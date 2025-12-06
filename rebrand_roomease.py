import os

# 1. BASE.HTML (Updates "UniNest" to "RoomEase" + keeps the logo font)
base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RoomEase | Student Living</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
    <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@800&display=swap" rel="stylesheet">
</head>
<body class="d-flex flex-column min-vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary py-3"> 
        <div class="container">
            <a class="navbar-brand" href="/" style="font-family: 'Montserrat', sans-serif; font-size: 1.8rem; letter-spacing: -1px;">
                <i class="bi bi-door-open-fill"></i> RoomEase
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto align-items-center">
                    <li class="nav-item"><a class="nav-link text-white mx-2" href="/rooms/">Browse</a></li>
                    {% if user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link text-white mx-2" href="/dashboard/">My Dashboard</a></li>
                        <li class="nav-item">
                            <form action="/accounts/logout/" method="post" class="d-inline">
                                {% csrf_token %}
                                <button class="btn btn-outline-light btn-sm ms-2" type="submit">Logout</button>
                            </form>
                        </li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link text-white mx-2" href="/accounts/login/">Login</a></li>
                        <li class="nav-item"><a class="btn btn-warning fw-bold text-dark ms-2" href="/register/">Post a Room</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <main class="flex-grow-1">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-dark text-white text-center py-4 mt-5">
        <div class="container">
            <h5 style="font-family: 'Montserrat', sans-serif;">RoomEase</h5>
            <p class="mb-0 text-muted small">© 2025 RoomEase Student Living.</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

# 2. HOME.HTML (Updates Hero Text to "RoomEase")
home_html = """{% extends 'base.html' %}
{% block content %}
<section class="text-white text-center py-5" style="background: linear-gradient(rgba(0,0,0,0.5), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?ixlib=rb-4.0.3&auto=format&fit=crop&w=1920&q=80') no-repeat center center; background-size: cover; padding-top: 100px !important; padding-bottom: 100px !important;">
    <div class="container">
        <h1 class="display-3 fw-bold mb-3" style="font-family: 'Montserrat', sans-serif;">Welcome to RoomEase</h1>
        <p class="lead fs-4 mb-5">The easiest way to find student accommodation in Melbourne.</p>
        
        <div class="card p-4 mx-auto shadow-lg border-0" style="max-width: 900px; border-radius: 15px; background: rgba(255, 255, 255, 0.95);">
            <form action="{% url 'room_list' %}" method="get" class="row g-3">
                <div class="col-md-4">
                    <div class="input-group">
                        <span class="input-group-text bg-white"><i class="bi bi-geo-alt"></i></span>
                        <input type="text" name="q" class="form-control" placeholder="Suburb (e.g. Carlton)">
                    </div>
                </div>
                <div class="col-md-3">
                    <select name="room_type" class="form-select">
                        <option value="">All Types</option>
                        <option value="private">Private Room</option>
                        <option value="shared">Shared Room</option>
                        <option value="studio">Studio</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <div class="input-group">
                        <span class="input-group-text bg-white">$</span>
                        <input type="number" name="max_price" class="form-control" placeholder="Max Budget">
                    </div>
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-primary w-100 fw-bold">Search</button>
                </div>
            </form>
        </div>
    </div>
</section>

<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4 border-bottom pb-2">
        <h3>Featured on RoomEase</h3>
        <a href="{% url 'room_list' %}" class="text-decoration-none">View All &rarr;</a>
    </div>
    
    <div class="row">
        {% for room in latest_rooms %}
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm border-0 hover-shadow transition">
                {% if room.image %}
                    <img src="{{ room.image.url }}" class="card-img-top" alt="{{ room.title }}" style="height: 220px; object-fit: cover;">
                {% else %}
                    <div class="bg-light text-secondary d-flex align-items-center justify-content-center" style="height: 220px;">
                        <i class="bi bi-image fs-1"></i>
                    </div>
                {% endif %}
                <div class="card-body">
                    <div class="d-flex justify-content-between mb-2">
                        <span class="badge bg-info text-dark">{{ room.get_room_type_display }}</span>
                        <span class="text-muted small"><i class="bi bi-clock"></i> {{ room.created_at|timesince }} ago</span>
                    </div>
                    <h5 class="card-title text-truncate">{{ room.title }}</h5>
                    <p class="card-text text-muted small"><i class="bi bi-geo-alt-fill text-danger"></i> {{ room.suburb }}</p>
                    <h5 class="text-primary fw-bold mb-0">${{ room.price_per_week }} <span class="small text-muted fw-normal">/week</span></h5>
                </div>
                <div class="card-footer bg-white border-top-0 pb-3">
                    <a href="{% url 'room_detail' room.pk %}" class="btn btn-outline-primary w-100">View Listing</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

# Write the files
with open('templates/base.html', 'w') as f:
    f.write(base_html)
    print("Updated: templates/base.html (Brand: RoomEase)")

with open('templates/core/home.html', 'w') as f:
    f.write(home_html)
    print("Updated: templates/core/home.html (Hero Text)")

print("✅ Rebrand to 'RoomEase' complete!")
