import React, { useContext } from "react";
import { Context } from "../store/appContext";


export const Alert = () => {
  const { store } = useContext(Context)

  return (
    <div className="row mt-5">
      <div className="container mt-5"></div>
      <div className={`text-center alert alert-${store.alert.back} ${store.alert.visible ? '' : 'd-none'}`} role="alert">
        {store.alert.text}
      </div>
    </div>
  )
}