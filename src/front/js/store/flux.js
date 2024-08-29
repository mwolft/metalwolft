const getState = ({ getStore, getActions, setStore }) => {
	return {
		store: {
			message: null,
			currentUser: null,
			isLoged: false,
			alert: {visible: false, back: 'danger', text: 'Mensaje del back'}
		},
		actions: {
            getMessage: async () => {
				const options = {
					headers: {'Content-Type' : 'application/json'},
					method: 'GET'
				}
				const response = await fetch(process.env.BACKEND_URL + "/api/hello", options);
				if (!response.ok) {
					console.log("Error loading message from backend", error);
					return
				}
				const data = await response.json();
				setStore({ message: data.message });
				return data;
		},
			setCurrentUser: (user) => {setStore({ currentUser: user })},
			setIsLoged: (isLogin) => {
				if (isLogin){
					setStore({ isLoged: true })
				} else {
					setStore({ isLoged: false })
					localStorage.removeItem("token")
					localStorage.removeItem("user")
				}
					
			},
            setAlert: (newAlert) => {setStore({ alert: newAlert })}
		}
	};
};

export default getState;
