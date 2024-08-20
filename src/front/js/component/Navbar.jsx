import React, { useContext } from "react";
import { Link } from "react-router-dom";
import { Context } from "../store/appContext";
import { Logout } from "./Logout.jsx";


export const Navbar = () => {
	const { store, actions } = useContext(Context);

	return (
		<nav className="navbar navbar-light bg-light">
			<div className="container">
				<Link to="/">
					<span className="navbar-brand mb-0 h1">React Boilerplate</span>
				</Link>
				<li className="nav-item d-flex align-items-center">
                            {store.isLoged ? 
                                <>
                                    <Link to="/">
                                        <Logout/>
                                    </Link>
                                </>
                            : 
                                <>
                                    <Link to="/login">
										<button type="button" className="btn btn-primary mx-2"><i className="fa-regular fa-user px-1"></i>Iniciar</button>
                                    </Link>
                                    <Link to="/sign-up">
										<button type="button" className="btn btn-light"><i className="fa-solid fa-arrow-right-to-bracket px-1"></i>SignUp</button>
                                    </Link>
                                </>
                            }
                        </li>
			</div>
		</nav>
	);
};
