#!/usr/bin/env python3
"""
Script to enhance services.html and contact.html with advanced features
"""

import re

# Enhanced CSS styles for both pages
enhanced_css = '''<style>
    /* ===== ADVANCED STYLES ===== */
    
    /* Hero Section */
    .page-hero {
        position: relative;
        overflow: hidden;
        min-height: 600px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .page-hero::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="20" cy="20" r="2" fill="rgba(255,255,255,0.1)"/><circle cx="80" cy="80" r="2" fill="rgba(255,255,255,0.1)"/></svg>');
        animation: slideBackground 20s linear infinite;
    }

    @keyframes slideBackground {
        0% { transform: translate(0, 0); }
        100% { transform: translate(100px, 100px); }
    }

    .page-hero-content {
        position: relative;
        z-index: 2;
        text-align: center;
        color: white;
    }

    .page-hero h1 {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        animation: slideInDown 1s ease-out;
    }

    .page-hero p {
        font-size: 1.5rem;
        opacity: 0.95;
        animation: slideInUp 1s ease-out 0.2s both;
    }

    /* Marquee Effect */
    .marquee-container {
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        color: white;
        overflow: hidden;
        padding: 1rem 0;
        margin: 2rem 0;
        position: relative;
    }

    .marquee {
        animation: marquee 30s linear infinite;
        white-space: nowrap;
        font-weight: 600;
        font-size: 1.1rem;
        letter-spacing: 1px;
    }

    @keyframes marquee {
        0% { transform: translateX(100%); }
        100% { transform: translateX(-100%); }
    }

    .marquee-container:hover .marquee {
        animation-play-state: paused;
    }

    /* Service Cards */
    .service-card {
        background: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        border: 2px solid transparent;
        position: relative;
        overflow: hidden;
    }

    .service-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 4px;
        background: linear-gradient(90deg, var(--primary), var(--accent), var(--secondary));
        animation: slideGradient 3s ease infinite;
    }

    @keyframes slideGradient {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .service-card:hover {
        transform: translateY(-15px) scale(1.02);
        border-color: var(--accent);
        box-shadow: 0 20px 50px rgba(0,0,0,0.15);
    }

    .service-icon {
        font-size: 3.5rem;
        margin-bottom: 1.5rem;
        display: inline-block;
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .service-card:hover .service-icon {
        transform: scale(1.2) rotateY(360deg);
        filter: drop-shadow(0 5px 15px rgba(0,0,0,0.2));
    }

    .service-card h4 {
        color: var(--primary);
        font-size: 1.4rem;
        margin-bottom: 0.8rem;
    }

    .service-card p {
        color: var(--text-dark);
        line-height: 1.6;
    }

    .service-card ul {
        margin-top: 1rem;
        padding-left: 1.5rem;
    }

    .service-card li {
        color: var(--text-light);
        margin-bottom: 0.5rem;
        transition: all 0.3s ease;
    }

    .service-card:hover li {
        color: var(--primary);
        transform: translateX(5px);
    }

    /* Premium Cards */
    .premium-card {
        background: linear-gradient(135deg, var(--accent) 0%, var(--secondary) 100%);
        color: white;
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .premium-card::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
        animation: pulse 3s ease-in-out infinite;
    }

    .premium-card:hover {
        transform: translateY(-20px);
        box-shadow: 0 25px 60px rgba(0,0,0,0.3);
    }

    .premium-badge {
        position: absolute;
        top: 1rem;
        right: 1rem;
        background: rgba(255,255,255,0.3);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 700;
        backdrop-filter: blur(10px);
    }

    .premium-card .service-icon {
        position: relative;
        z-index: 2;
        filter: drop-shadow(0 2px 10px rgba(0,0,0,0.2));
    }

    .premium-card h4,
    .premium-card p {
        position: relative;
        z-index: 2;
        color: white;
    }

    /* Contact Form */
    .contact-section {
        padding: 4rem 2rem;
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.05) 0%, rgba(14, 165, 233, 0.05) 100%);
    }

    .contact-container {
        max-width: 1200px;
        margin: 0 auto;
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 3rem;
        align-items: start;
    }

    .contact-info {
        padding: 2rem;
    }

    .contact-info h2 {
        font-size: 2.2rem;
        color: var(--primary);
        margin-bottom: 1rem;
    }

    .contact-info p {
        color: var(--text-light);
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }

    .contact-details {
        margin-bottom: 2rem;
    }

    .detail-item {
        display: flex;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
        padding: 1rem;
        background: white;
        border-radius: 10px;
        transition: all 0.3s ease;
        border-left: 4px solid var(--accent);
    }

    .detail-item:hover {
        transform: translateX(10px);
        box-shadow: 0 5px 20px rgba(0,0,0,0.1);
    }

    .detail-icon {
        font-size: 1.8rem;
        flex-shrink: 0;
    }

    .detail-item h4 {
        color: var(--primary);
        font-weight: 600;
        margin-bottom: 0.3rem;
    }

    .detail-item p {
        margin: 0;
        color: var(--text-dark);
        font-size: 0.95rem;
    }

    .social-icon {
        display: inline-block;
        padding: 0.8rem 1.5rem;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        text-decoration: none;
        border-radius: 50px;
        transition: all 0.3s ease;
        font-weight: 600;
    }

    .social-icon:hover {
        transform: translateY(-5px) scale(1.05);
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }

    /* Contact Form */
    .contact-form {
        background: white;
        padding: 2.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }

    .contact-form h3 {
        color: var(--primary);
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
    }

    .form-group {
        margin-bottom: 1.5rem;
    }

    .form-group label {
        display: block;
        color: var(--text-dark);
        font-weight: 600;
        margin-bottom: 0.5rem;
    }

    .form-group input,
    .form-group textarea {
        width: 100%;
        padding: 0.8rem;
        border: 2px solid var(--light);
        border-radius: 8px;
        font-family: inherit;
        transition: all 0.3s ease;
    }

    .form-group input:focus,
    .form-group textarea:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
        transform: translateY(-2px);
    }

    .form-submit {
        width: 100%;
        padding: 1rem;
        background: linear-gradient(135deg, var(--primary), var(--secondary));
        color: white;
        border: none;
        border-radius: 8px;
        font-size: 1.1rem;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    .form-submit:hover {
        transform: translateY(-3px);
        box-shadow: 0 15px 40px rgba(0,0,0,0.2);
    }

    .form-submit:active {
        transform: translateY(-1px);
    }

    /* FAQ Section */
    .faq-section {
        padding: 5rem 2rem;
        background: white;
    }

    .faq-container {
        max-width: 800px;
        margin: 3rem auto 0;
        display: grid;
        gap: 1.5rem;
    }

    .faq-item {
        background: linear-gradient(135deg, rgba(30, 58, 138, 0.05) 0%, rgba(14, 165, 233, 0.05) 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid var(--accent);
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .faq-item:hover {
        transform: translateX(10px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        border-left-color: var(--primary);
    }

    .faq-item h4 {
        color: var(--primary);
        font-size: 1.2rem;
        margin-bottom: 0.8rem;
    }

    .faq-item p {
        color: var(--text-dark);
        margin: 0;
        line-height: 1.6;
    }

    /* Services Grid */
    .services-grid {
        max-width: 1200px;
        margin: 3rem auto 0;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
        gap: 2rem;
    }

    .premium-grid {
        max-width: 1200px;
        margin: 3rem auto 0;
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
    }

    /* Section Header */
    .section-header {
        text-align: center;
        margin-bottom: 2rem;
    }

    .section-header h2 {
        font-size: 2.5rem;
        color: var(--primary);
        margin-bottom: 0.5rem;
    }

    .section-header p {
        font-size: 1.1rem;
        color: var(--text-light);
    }

    /* Services Showcase */
    .services-showcase {
        padding: 5rem 2rem;
        background: white;
    }

    .service-category {
        margin-bottom: 3rem;
    }

    /* Animation Classes */
    @keyframes slideInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes slideInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeDown {
        from {
            opacity: 0;
            transform: translateY(-20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); opacity: 0.5; }
        50% { transform: scale(1.1); opacity: 0.3; }
    }

    .animate-fade-down {
        animation: fadeDown 0.8s ease-out;
    }

    .animate-slide-left {
        animation: slideInLeft 0.8s ease-out;
    }

    .animate-slide-right {
        animation: slideInRight 0.8s ease-out;
    }

    .animate-feature {
        animation: featureBounce 0.6s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes featureBounce {
        0% {
            opacity: 0;
            transform: translateY(30px) scale(0.9);
        }
        100% {
            opacity: 1;
            transform: translateY(0) scale(1);
        }
    }

    @media (max-width: 768px) {
        .contact-container {
            grid-template-columns: 1fr;
        }

        .page-hero h1 {
            font-size: 2rem;
        }

        .services-grid,
        .premium-grid {
            grid-template-columns: 1fr;
        }
    }
</style>'''

print(enhanced_css)
