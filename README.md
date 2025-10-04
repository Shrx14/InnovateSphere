# InnovateSphere

InnovateSphere is a full-stack web application designed to help users generate innovative project ideas, manage their profiles, and collaborate on creative endeavors. The platform features user authentication, project idea generation, and a modern, responsive user interface.

## Features

- **User Authentication**: Secure registration and login with email/password
- **Two-Factor Authentication (2FA)**: SMS-based 2FA for enhanced security
- **Project Idea Generation**: AI-powered suggestions for innovative projects
- **User Profiles**: Customizable profiles with skill levels and preferred domains
- **Responsive Design**: Modern UI built with React and Tailwind CSS
- **RESTful API**: Flask-based backend with comprehensive API endpoints

## Tech Stack

### Backend
- **Flask**: Python web framework
- **SQLAlchemy**: ORM for database management
- **PostgreSQL**: Primary database
- **Twilio**: SMS services for 2FA
- **bcrypt**: Password hashing
- **pyotp**: TOTP for 2FA

### Frontend
- **React**: JavaScript library for building user interfaces
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API requests

### Infrastructure
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration

## Project Structure

```
innovatesphere/
├── backend/                 # Flask API backend
│   ├── app.py              # Main application file
│   ├── migrations.py       # Database migrations
│   ├── requirements.txt    # Python dependencies
│   └── test_twilio.py      # Twilio testing utilities
├── frontend/               # React frontend application
│   ├── public/            # Static assets
│   ├── src/               # Source code
│   │   ├── components/    # React components
│   │   ├── config.js      # Configuration
│   │   └── App.js         # Main app component
│   └── package.json       # Node.js dependencies
├── docker-compose.yml      # Docker Compose configuration
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd innovatesphere
   ```

2. **Environment Setup**
   - Copy `.env.example` to `.env` and configure your environment variables
   - For backend: Set up database credentials, Twilio API keys, etc.
   - For frontend: Configure API endpoints

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

   This will start:
   - Backend API on `http://localhost:5000`
   - Frontend on `http://localhost:3000`
   - PostgreSQL database

### Manual Setup (Alternative)

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
flask run
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## API Documentation

### Authentication Endpoints

- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/change-password` - Change password
- `POST /api/setup-phone` - Setup phone for 2FA
- `POST /api/verify-phone` - Verify phone number
- `POST /api/setup-2fa` - Enable 2FA
- `POST /api/verify-2fa` - Verify 2FA code
- `POST /api/disable-2fa` - Disable 2FA

### Health Check

- `GET /api/health` - API health check

## Development

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

- Backend: Follow PEP 8 guidelines
- Frontend: Use ESLint and Prettier

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Flask and React
- SMS services powered by Twilio
- UI components styled with Tailwind CSS
