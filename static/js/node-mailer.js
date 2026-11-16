const nodemailer = require("nodemailer");

const html = `

    <h1>HERE IS YOUR REMINDER TO TAKE YOUR MEDS</h1>
    <p>you're welcome.</p>
`;

// Create a transporter using SMTP
const authentication_ = nodemailer.createTransport({
    host: 'smtp.gmail.com',
    port: 465,
    secure: true,
    auth: {
        user: 'iamerror98@gmail.com',

        //put the email and password for the email here. Erased the previous one because I do not want to be hacked.
        pass: 'zufn gdxh ingl gbws',
  }
});

const mail_options = {
    from: 'iamerror98@gmail.com',
    //You can add multiple recipients by doing this...
    // to: ['recipient1@example.com', 'recipient2@example.com'],
    to: 'jhamon@unomaha.edu',
    subject: 'Medication Reminder',
    html: html
};   

authentication_.sendMail(mail_options, (err,info)=> {
    if(err) {
        console.log(err)
    } else {
        console.log(info)
        }
    });