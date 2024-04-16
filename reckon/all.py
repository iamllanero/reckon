import build
import flatten
import txns
import price
import tax_hifo

if __name__ == '__main__':

    print("Running all scripts")

    print("Running build.py")
    build.main()

    print("Running flatten.py")
    flatten.main()

    print("Running txns.py")
    txns.main()

    print("Running price.py")
    price.main()

    print("Running tax_hifo.py")
    tax_hifo.main()
