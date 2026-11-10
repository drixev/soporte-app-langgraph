def acumular(actual: list, nuevo: list | None) -> list:
   """Reducer propio: None reinicia la lista; una lista se agrega al final.""" 
   if nuevo is None:
       return []
   return actual + nuevo
