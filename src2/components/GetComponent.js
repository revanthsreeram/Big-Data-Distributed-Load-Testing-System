import React, { useEffect, useState, useRef } from 'react';

const LiveComponent1 = () => {
  const [receivedData, setReceivedData] = useState({});
  const socketRef = useRef(null);

  useEffect(() => {
    socketRef.current = new WebSocket('ws://localhost:8003/ws2');

    socketRef.current.onopen = () => {
      console.log('WebSocket connected');
    };

    socketRef.current.onmessage = (event) => {
      const newData = JSON.parse(event.data);
      console.log(newData);

      setReceivedData((prevData) => {
        return { ...prevData, [newData.node_id]: newData };
      });
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
      <h2>Heartbeat Data</h2>
      {Object.keys(receivedData).map((nodeId) => (
        <p key={nodeId} className={`${nodeId}`}>
          {JSON.stringify(receivedData[nodeId])}
        </p>
      ))}
    </div>
  );
};

export default LiveComponent1;

