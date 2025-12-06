import os

# 1. NEW BASE.HTML (Navigation Bar & Footer)
base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>UniNest | Room Rentals</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
</head>
<body class="d-flex flex-column min-vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary"> 
        <div class="container">
            <a class="navbar-brand fw-bold" href="/">🪹 UniNest <span class="fs-6 fw-light">| Room Rentals</span></a>
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ms-auto">
                    <li class="nav-item"><a class="nav-link text-white" href="/rooms/">Browse Rooms</a></li>
                    {% if user.is_authenticated %}
                        <li class="nav-item"><a class="nav-link text-white" href="/dashboard/">Dashboard</a></li>
                        <li class="nav-item">
                            <form action="/accounts/logout/" method="post" class="d-inline">
                                {% csrf_token %}
                                <button class="btn nav-link text-white" type="submit">Logout</button>
                            </form>
                        </li>
                    {% else %}
                        <li class="nav-item"><a class="nav-link text-white" href="/accounts/login/">Login</a></li>
                        <li class="nav-item"><a class="btn btn-light text-primary ms-2" href="/register/">Post a Room</a></li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <main class="flex-grow-1">
        {% block content %}{% endblock %}
    </main>

    <footer class="bg-dark text-white text-center py-4 mt-4">
        <div class="container">
            <h5>UniNest</h5>
            <p class="mb-0 text-muted small">© 2025 UniNest Room Rentals. All rights reserved.</p>
        </div>
    </footer>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>"""

# 2. NEW HOME.HTML (Hero Section)
home_html = """{% extends 'base.html' %}
{% block content %}
<section class="bg-primary text-white text-center py-5" style="background: linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://source.unsplash.com/1600x900/?melbourne,apartment') no-repeat center center; background-size: cover;">
    <div class="container py-5">
        <h1 class="display-3 fw-bold">UniNest</h1>
        <p class="lead fs-3">Room Rentals in Melbourne</p>
        <p class="mb-4">Find your perfect student accommodation or shared house today.</p>
        
        <div class="card p-4 mt-4 text-dark mx-auto shadow-lg" style="max-width: 800px; border-radius: 15px;">
            <form action="{% url 'room_list' %}" method="get" class="row g-2">
                <div class="col-md-4">
                    <input type="text" name="q" class="form-control form-control-lg" placeholder="Suburb (e.g. Clayton)">
                </div>
                <div class="col-md-3">
                    <select name="room_type" class="form-select form-select-lg">
                        <option value="">Any Type</option>
                        <option value="private">Private</option>
                        <option value="shared">Shared</option>
                        <option value="studio">Studio</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <input type="number" name="max_price" class="form-control form-control-lg" placeholder="Max $">
                </div>
                <div class="col-md-2">
                    <button type="submit" class="btn btn-success btn-lg w-100">Search</button>
                </div>
            </form>
        </div>
    </div>
</section>

<div class="container py-5">
    <h3 class="mb-4 border-bottom pb-2">Latest on UniNest</h3>
    <div class="row">
        {% for room in latest_rooms %}
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm hover-shadow transition">
                {% if room.image %}
                    <img src="{{ room.image.url }}" class="card-img-top" alt="{{ room.title }}" style="height: 220px; object-fit: cover;">
                {% else %}
                    <div class="bg-secondary text-white d-flex align-items-center justify-content-center" style="height: 220px;">No Image</div>
                {% endif %}
                <div class="card-body">
                    <h5 class="card-title">{{ room.title }}</h5>
                    <p class="card-text text-muted"><i class="bi bi-geo-alt"></i> {{ room.suburb }}</p>
                    <h6 class="text-primary fw-bold">${{ room.price_per_week }} <span class="small text-muted">/week</span></h6>
                </div>
                <div class="card-footer bg-white border-top-0 pb-3">
                    <a href="{% url 'room_detail' room.pk %}" class="btn btn-outline-primary w-100">View Details</a>
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}"""

with open('templates/base.html', 'w') as f:
    f.write(base_html)
    print("Updated: templates/base.html")

with open('templates/core/home.html', 'w') as f:
    f.write(home_html)
    print("Updated: templates/core/home.html")

print("✅ Rebranding to 'UniNest' complete!")
