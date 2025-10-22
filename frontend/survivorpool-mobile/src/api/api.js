import axios from "axios";

const API = axios.create({
    baseURL: "http://192.168.1.168:8001"
    
});
console.log(API.baseURL);
export default API;

