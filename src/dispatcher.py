import fibonacci
import provenance

provenance.register(fibonacci.fib)

print fibonacci.fib(50)
print provenance.cache