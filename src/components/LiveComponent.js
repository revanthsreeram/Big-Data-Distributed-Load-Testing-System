import React, { useEffect, useState, useRef } from 'react';

const LiveComponent1 = () => {
  const [receivedData, setReceivedData] = useState('');
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket('ws://localhost:8002/ws');

    socketRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    socketRef.current.onmessage = (event) => {
      const datas = JSON.parse(event.data);
      console.log(datas);
      setReceivedData(datas); // Convert data to an object
    };

    socketRef.current.onclose = () => {
      console.log('WebSocket disconnected');
    };

    return () => {
      if (socketRef.current !== null) {
        socketRef.current.close();
      }
    };
  }, []);

  return (
    <div>
      <h2>metric Data</h2>
      <p>{JSON.stringify(receivedData)}</p>
    </div>
  );
};

export default LiveComponent1;

