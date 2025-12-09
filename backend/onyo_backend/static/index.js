if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("static/service_worker.js").then(registration => {
        console.log("SW Registered!");
    }).catch(error => {
        console.log("SW Registration Failed", error);
    });
} else {
    console.log("Not supported");
}