#### Join the Speakeasy @ https://speakeaisy.vercel.app

# SpeakeAIsy

A messaging app that translates any messages sent to you to your set language, allowing for communication between anyone by breaking the language barrier.

# Features

- Asynchronous
- Real-time communication and updates
- User Authentication and JWT Tokens
- Support for 62 languages
- Sign up/Log in
- Forgot Password
- Email Verification
- Toast Notifications
- Natural grouping of messages and time/date separations between messages in UI
- User settings
- Group chats and 1-on-1 chats
- Cropping of images

# Frontend

The frontend is built with SvelteKit and TypeScript. UI is mobile-friendly. WebSocket communication is used to update state and UI in real-time. All form data is validated and supports image uploads. Appropriate errors are displayed dynamically or using toast notifications. Secure cookies are used to identify sessions.

# Backend

The backend is built with FastAPI. It consists of API endpoints and a WebSocket endpoint. All possible endpoints and functions are asynchronous to support concurrency and efficiency. All endpoints use Pydantic for data validation and response models, enforcing consistency and safety. Secure endpoints check for user auth before being accessible. Dependency injection is used in endpoints when possible. Real-time communication and updates for the UI are done using WebSockets and Redis Pub/Sub. Redis is also used for caching data. An SMTP server is set up to send emails. GPT-4 with memory and context is used to translate messages. Testing is done with Pytest.

# Database

PostgreSQL is used. Asynchronous SQLAlchemy is used to operate on the database to support concurrency. SSL connection is used for secure database communication. Alembic is used for database migrations to ensure database repeatability and consistency across platforms.

# Deployment Infrastructure

- Backend deployed on AWS EC2 with an NGINX reverse proxy and TLS Certificate for HTTPS
- Systemd service for continuous deployment
- AWS S3 for image storage
- AWS RDS for PostgreSQL
- AWS ElastiCache for Redis
- Frontend deployed on Vercel

# Optimizations

- Concurrency
- Background Tasks
- Database indexing
- Database connection pooling
- Scheduled database cleanups
- Virtual scrolling of conversations list
- Lazy loading of chat messages
- Caching
- API Rate limiting and reCaptcha
- Presigned URLs for fetching and posting images to S3
