// 是否为开发阶段
const DEV = process.env.NODE_ENV == 'development'
export const IP = DEV ? '127.0.0.1:5000' : '192.168.23.133:5000'

console.log()