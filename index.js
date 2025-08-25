const signalR = require('@microsoft/signalr');

async function start() {
  try {
    // Fetch negotiate connection info
    const negotiateResponse = await fetch('https://func-adnocgpt.azurewebsites.net/api/negotiate', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (!negotiateResponse.ok) {
      throw new Error(`Negotiate request failed with status: ${negotiateResponse.status}`);
    }
    
    const negotiateData = await negotiateResponse.json();

    // Build SignalR connection
    const connection = new signalR.HubConnectionBuilder()
      .withUrl(negotiateData.url, {
        accessTokenFactory: () => negotiateData.accessToken
      })
      .withAutomaticReconnect()
      .build();

    // Receive messages on 'ReceiveMessage' event (or your event name)
    connection.on('NewMessage', (message) => {
      console.log('Received message:', message);
    });

    // Start connection
    await connection.start();
    console.log('SignalR client connected.');
  } catch (error) {
    console.error('SignalR connection error:', error);
    throw error;
  }
}

start().catch(err => console.error(err));
