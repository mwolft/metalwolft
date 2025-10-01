import React from 'react';

export const ReturnsPolicy = () => {
    return (
        <>
            <div className="container" style={{ marginTop: '65px' }}>
                <h1 className='h1-categories'>Política de Devoluciones y Garantías</h1>

                <p className='mb-5'>
                    En MetalWolft fabricamos cada reja de forma individual y personalizada según las medidas,
                    especificaciones y acabados seleccionados por el cliente. Por este motivo, nuestra política
                    de devoluciones se ajusta a la normativa española y europea sobre bienes confeccionados a
                    medida (art. 103.c del Real Decreto Legislativo 1/2007).
                </p>

                <h2 className="h2-categories mb-3">1. Productos Personalizados</h2>
                <p>
                    De acuerdo con la ley, los productos fabricados conforme a las especificaciones del consumidor o claramente personalizados <u>no admiten desistimiento ni devolución</u>, salvo en caso de defecto o error comprobado en la fabricación o el acabado.
                </p>
                <p className='mb-5'>
                    Antes de confirmar tu pedido, deberás aceptar expresamente esta condición, entendiendo que las rejas se fabrican a medida
                    y no pueden ser revendidas o reutilizadas.
                </p>

                <h2 className="h2-categories mb-3">2. Tolerancias de Fabricación</h2>
                <p>
                    Debido a la naturaleza artesanal del proceso, pueden existir pequeñas variaciones respecto a las medidas solicitadas.
                    Estas diferencias se consideran normales y no constituyen un defecto.
                </p>
                <ul className='mb-5'>
                    <li>Altura: tolerancia máxima ±5 mm.</li>
                    <li>Ancho: tolerancia máxima ±2 mm.</li>
                </ul>

                <h2 className="h2-categories mb-3">3. Acabado y Pintura</h2>
                <p>
                    Cada reja se pinta individualmente, por lo que pueden presentarse pequeñas marcas o ligeras variaciones de tono.
                    No obstante, si consideras que el acabado recibido presenta defectos evidentes (desconchados, burbujas, manchas),
                    podrás notificárnoslo mediante nuestro <a href="/formulario-incidencias">Formulario de Incidencias</a> en un plazo máximo de 48 horas desde la recepción.
                </p>
                <p>
                    Analizaremos cada caso y podremos ofrecer, según proceda:
                </p>
                <ul className='mb-5'>
                    <li>Envío gratuito de un kit de retoque con pintura original y lijas.</li>
                    <li>Reposición parcial o total del producto si el defecto es significativo y comprobado.</li>
                    <li>Compensación económica si el cliente decide conservar el producto.</li>
                </ul>

                <h2 className="h2-categories mb-3">4. Procedimiento para Solicitar una Revisión</h2>
                <p className='mb-5'>
                    Si detectas un defecto o error en la fabricación, deberás comunicarlo a través del formulario de incidencias
                    adjuntando fotografías claras del producto y una descripción del problema.
                    También puedes contactarnos por correo electrónico a <a href="mailto:admin@metalwolft.com">admin@metalwolft.com</a> indicando tu número de pedido.
                </p>

                <h2 className="h2-categories mb-3">5. Productos Instalados o Manipulados</h2>
                <p>
                    Las rejas, puertas y cerramientos fabricados a medida no admiten devolución una vez instalados o manipulados.
                    Si detectas cualquier incidencia en el acabado, medidas o estado del producto, es imprescindible comunicarlo
                    antes de su instalación y conservar el embalaje original.
                </p>
                <p className='mb-5'>
                    Una vez instalado el producto, se entenderá que el cliente acepta su conformidad con las medidas, el color,
                    el tipo de anclaje y el acabado recibido. No se aceptarán reclamaciones ni devoluciones derivadas de daños,
                    defectos o ajustes surgidos tras la instalación o manipulación, salvo que se acredite un defecto de fabricación
                    existente en el momento de la entrega.
                </p>

                <h2 className="h2-categories mb-3">6. Costes y Plazos</h2>
                <p className='mb-5'>
                    Una vez evaluada la incidencia, MetalWolft se hará cargo de los gastos de transporte si el defecto es confirmado.
                    En cualquier otro caso, los gastos de devolución correrán a cargo del cliente.
                </p>

                <h2 className="h2-categories mb-3">7. Garantía Legal</h2>
                <p className='mb-5'>
                    Todos nuestros productos cuentan con la garantía legal de conformidad aplicable (mínimo 2 años).
                    Esta garantía cubre defectos de fabricación o materiales, pero no daños derivados de un uso inadecuado,
                    instalación incorrecta o falta de mantenimiento.
                </p>

                <h2 className="h2-categories mb-3">8. Cancelación de Pedidos</h2>
                <p className='mb-5'>
                    Los pedidos podrán cancelarse únicamente antes de iniciar la fabricación.
                    Una vez en proceso, no será posible su anulación debido al carácter personalizado del producto.
                </p>
            </div>
        </>
    );
};
