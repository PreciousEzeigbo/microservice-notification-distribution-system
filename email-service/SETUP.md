# Email Service Setup Instructions

## Required Dependencies

Run this command to install all required packages:

\`\`\`bash
npm install --save @nestjs/config @nestjs/axios amqplib nodemailer handlebars
npm install --save-dev @types/amqplib @types/nodemailer
\`\`\`

## Configuration

1. Copy .env.example to .env:
\`\`\`bash
cp .env.example .env
\`\`\`

2. Update .env with your actual configuration values

## Next Steps

1. Install dependencies (see above)
2. Configure environment variables
3. Start RabbitMQ server
4. Run: npm run start:dev

## Full documentation available in README.md
