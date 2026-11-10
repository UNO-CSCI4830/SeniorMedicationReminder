require('dotenv').config();
const twilio = require('twilio');

// Initialize the Twilio client using your environment variables
const account_SID = process.env.TWILIO_ACCOUNT_SID;
const auth_TOKEN = process.env.TWILIO_AUTH_TOKEN;
const client = new twilio(account_SID, auth_TOKEN);

async function sendSMS() {
  try {
    const message = await client.messages.create({
      body: 'sms_appointment_reminders',
      from: process.env.TWILIO_NUMBER, // Your Twilio phone number
      to: '+14027085913'               // The recipient's mobile number (must include country code)
    });

    console.log(`Success! Message sent with SID: ${message.sid}`);
  } catch (error) {
    console.error(`Failed to send message: ${error.message}`);
  }
}

sendSMS();