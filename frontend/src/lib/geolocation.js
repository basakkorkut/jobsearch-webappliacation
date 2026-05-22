export function getCurrentCity() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation desteklenmiyor'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      async ({ coords: { latitude, longitude } }) => {
        try {
          const res = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`,
            { headers: { 'Accept-Language': 'en' } }
          )
          const data = await res.json()
          const city =
            data.address?.city ||
            data.address?.town ||
            data.address?.county ||
            null
          resolve(city)
        } catch {
          reject(new Error('Konum çözümlenemedi'))
        }
      },
      (err) => reject(err),
      { timeout: 8000 }
    )
  })
}
