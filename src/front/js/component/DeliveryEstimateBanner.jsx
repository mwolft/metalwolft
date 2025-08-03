import React from 'react';

export const DeliveryEstimateBanner = () => {
    return (
        <div style={styles.banner}>
            Fecha estimada de entrega: entre el 25 y el 31 de agosto.
        </div>
    );
};

const styles = {
    banner: {
        backgroundColor: '#f5f5f5',
        padding: '10px',
        textAlign: 'center',
        fontWeight: 'bold',
        borderRadius: '8px',
        margin: '10px 0'
    }
};
