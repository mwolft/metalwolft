import React from "react";
import { Helmet } from "react-helmet";


export const Error404 = () => {

  return (
    <>
      <Helmet>
        <meta name="robots" content="noindex, nofollow" />
        <meta name="theme-color" content="#ff324d" />
      </Helmet>
      <div className="container" style={{ marginTop: '100px' }}>
        <h1 className="text-center text-danger">Error 404 - Page not found</h1>
      </div>
    </>
  )
}
