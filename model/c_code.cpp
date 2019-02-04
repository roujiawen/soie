#ifdef __CPLUSPLUS__
extern "C" {
#endif

#ifndef __GNUC__
#pragma warning(disable: 4275)
#pragma warning(disable: 4101)

#endif
#include "Python.h"
#include "compile.h"
#include "frameobject.h"
#include <complex>
#include <math.h>
#include <string>
#include "scxx/object.h"
#include "scxx/list.h"
#include "scxx/tuple.h"
#include "scxx/dict.h"
#include <iostream>
#include <stdio.h>
#include "numpy/arrayobject.h"




// global None value for use in functions.
namespace py {
object None = object(Py_None);
}

const char* find_type(PyObject* py_obj)
{
    if(py_obj == NULL) return "C NULL value";
    if(PyCallable_Check(py_obj)) return "callable";
    if(PyString_Check(py_obj)) return "string";
    if(PyInt_Check(py_obj)) return "int";
    if(PyFloat_Check(py_obj)) return "float";
    if(PyDict_Check(py_obj)) return "dict";
    if(PyList_Check(py_obj)) return "list";
    if(PyTuple_Check(py_obj)) return "tuple";
    if(PyFile_Check(py_obj)) return "file";
    if(PyModule_Check(py_obj)) return "module";

    //should probably do more intergation (and thinking) on these.
    if(PyCallable_Check(py_obj) && PyInstance_Check(py_obj)) return "callable";
    if(PyInstance_Check(py_obj)) return "instance";
    if(PyCallable_Check(py_obj)) return "callable";
    return "unknown type";
}

void throw_error(PyObject* exc, const char* msg)
{
 //printf("setting python error: %s\n",msg);
  PyErr_SetString(exc, msg);
  //printf("throwing error\n");
  throw 1;
}

void handle_bad_type(PyObject* py_obj, const char* good_type, const char* var_name)
{
    char msg[500];
    sprintf(msg,"received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);
}

void handle_conversion_error(PyObject* py_obj, const char* good_type, const char* var_name)
{
    char msg[500];
    sprintf(msg,"Conversion Error:, received '%s' type instead of '%s' for variable '%s'",
            find_type(py_obj),good_type,var_name);
    throw_error(PyExc_TypeError,msg);
}


class int_handler
{
public:
    int convert_to_int(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyInt_Check(py_obj))
            handle_conversion_error(py_obj,"int", name);
        return (int) PyInt_AsLong(py_obj);
    }

    int py_to_int(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyInt_Check(py_obj))
            handle_bad_type(py_obj,"int", name);
        
        return (int) PyInt_AsLong(py_obj);
    }
};

int_handler x__int_handler = int_handler();
#define convert_to_int(py_obj,name) \
        x__int_handler.convert_to_int(py_obj,name)
#define py_to_int(py_obj,name) \
        x__int_handler.py_to_int(py_obj,name)


PyObject* int_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class float_handler
{
public:
    double convert_to_float(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyFloat_Check(py_obj))
            handle_conversion_error(py_obj,"float", name);
        return PyFloat_AsDouble(py_obj);
    }

    double py_to_float(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyFloat_Check(py_obj))
            handle_bad_type(py_obj,"float", name);
        
        return PyFloat_AsDouble(py_obj);
    }
};

float_handler x__float_handler = float_handler();
#define convert_to_float(py_obj,name) \
        x__float_handler.convert_to_float(py_obj,name)
#define py_to_float(py_obj,name) \
        x__float_handler.py_to_float(py_obj,name)


PyObject* float_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class complex_handler
{
public:
    std::complex<double> convert_to_complex(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyComplex_Check(py_obj))
            handle_conversion_error(py_obj,"complex", name);
        return std::complex<double>(PyComplex_RealAsDouble(py_obj),PyComplex_ImagAsDouble(py_obj));
    }

    std::complex<double> py_to_complex(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyComplex_Check(py_obj))
            handle_bad_type(py_obj,"complex", name);
        
        return std::complex<double>(PyComplex_RealAsDouble(py_obj),PyComplex_ImagAsDouble(py_obj));
    }
};

complex_handler x__complex_handler = complex_handler();
#define convert_to_complex(py_obj,name) \
        x__complex_handler.convert_to_complex(py_obj,name)
#define py_to_complex(py_obj,name) \
        x__complex_handler.py_to_complex(py_obj,name)


PyObject* complex_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class unicode_handler
{
public:
    Py_UNICODE* convert_to_unicode(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyUnicode_Check(py_obj))
            handle_conversion_error(py_obj,"unicode", name);
        return PyUnicode_AS_UNICODE(py_obj);
    }

    Py_UNICODE* py_to_unicode(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyUnicode_Check(py_obj))
            handle_bad_type(py_obj,"unicode", name);
        Py_XINCREF(py_obj);
        return PyUnicode_AS_UNICODE(py_obj);
    }
};

unicode_handler x__unicode_handler = unicode_handler();
#define convert_to_unicode(py_obj,name) \
        x__unicode_handler.convert_to_unicode(py_obj,name)
#define py_to_unicode(py_obj,name) \
        x__unicode_handler.py_to_unicode(py_obj,name)


PyObject* unicode_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class string_handler
{
public:
    std::string convert_to_string(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyString_Check(py_obj))
            handle_conversion_error(py_obj,"string", name);
        return std::string(PyString_AsString(py_obj));
    }

    std::string py_to_string(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyString_Check(py_obj))
            handle_bad_type(py_obj,"string", name);
        Py_XINCREF(py_obj);
        return std::string(PyString_AsString(py_obj));
    }
};

string_handler x__string_handler = string_handler();
#define convert_to_string(py_obj,name) \
        x__string_handler.convert_to_string(py_obj,name)
#define py_to_string(py_obj,name) \
        x__string_handler.py_to_string(py_obj,name)


               PyObject* string_to_py(std::string s)
               {
                   return PyString_FromString(s.c_str());
               }
               
class list_handler
{
public:
    py::list convert_to_list(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyList_Check(py_obj))
            handle_conversion_error(py_obj,"list", name);
        return py::list(py_obj);
    }

    py::list py_to_list(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyList_Check(py_obj))
            handle_bad_type(py_obj,"list", name);
        
        return py::list(py_obj);
    }
};

list_handler x__list_handler = list_handler();
#define convert_to_list(py_obj,name) \
        x__list_handler.convert_to_list(py_obj,name)
#define py_to_list(py_obj,name) \
        x__list_handler.py_to_list(py_obj,name)


PyObject* list_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class dict_handler
{
public:
    py::dict convert_to_dict(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyDict_Check(py_obj))
            handle_conversion_error(py_obj,"dict", name);
        return py::dict(py_obj);
    }

    py::dict py_to_dict(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyDict_Check(py_obj))
            handle_bad_type(py_obj,"dict", name);
        
        return py::dict(py_obj);
    }
};

dict_handler x__dict_handler = dict_handler();
#define convert_to_dict(py_obj,name) \
        x__dict_handler.convert_to_dict(py_obj,name)
#define py_to_dict(py_obj,name) \
        x__dict_handler.py_to_dict(py_obj,name)


PyObject* dict_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class tuple_handler
{
public:
    py::tuple convert_to_tuple(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyTuple_Check(py_obj))
            handle_conversion_error(py_obj,"tuple", name);
        return py::tuple(py_obj);
    }

    py::tuple py_to_tuple(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyTuple_Check(py_obj))
            handle_bad_type(py_obj,"tuple", name);
        
        return py::tuple(py_obj);
    }
};

tuple_handler x__tuple_handler = tuple_handler();
#define convert_to_tuple(py_obj,name) \
        x__tuple_handler.convert_to_tuple(py_obj,name)
#define py_to_tuple(py_obj,name) \
        x__tuple_handler.py_to_tuple(py_obj,name)


PyObject* tuple_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class file_handler
{
public:
    FILE* convert_to_file(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyFile_Check(py_obj))
            handle_conversion_error(py_obj,"file", name);
        return PyFile_AsFile(py_obj);
    }

    FILE* py_to_file(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyFile_Check(py_obj))
            handle_bad_type(py_obj,"file", name);
        Py_XINCREF(py_obj);
        return PyFile_AsFile(py_obj);
    }
};

file_handler x__file_handler = file_handler();
#define convert_to_file(py_obj,name) \
        x__file_handler.convert_to_file(py_obj,name)
#define py_to_file(py_obj,name) \
        x__file_handler.py_to_file(py_obj,name)


               PyObject* file_to_py(FILE* file, const char* name,
                                    const char* mode)
               {
                   return (PyObject*) PyFile_FromFile(file,
                     const_cast<char*>(name),
                     const_cast<char*>(mode), fclose);
               }
               
class instance_handler
{
public:
    py::object convert_to_instance(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !PyInstance_Check(py_obj))
            handle_conversion_error(py_obj,"instance", name);
        return py::object(py_obj);
    }

    py::object py_to_instance(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyInstance_Check(py_obj))
            handle_bad_type(py_obj,"instance", name);
        
        return py::object(py_obj);
    }
};

instance_handler x__instance_handler = instance_handler();
#define convert_to_instance(py_obj,name) \
        x__instance_handler.convert_to_instance(py_obj,name)
#define py_to_instance(py_obj,name) \
        x__instance_handler.py_to_instance(py_obj,name)


PyObject* instance_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class numpy_size_handler
{
public:
    void conversion_numpy_check_size(PyArrayObject* arr_obj, int Ndims,
                                     const char* name)
    {
        if (arr_obj->nd != Ndims)
        {
            char msg[500];
            sprintf(msg,"Conversion Error: received '%d' dimensional array instead of '%d' dimensional array for variable '%s'",
                    arr_obj->nd,Ndims,name);
            throw_error(PyExc_TypeError,msg);
        }
    }

    void numpy_check_size(PyArrayObject* arr_obj, int Ndims, const char* name)
    {
        if (arr_obj->nd != Ndims)
        {
            char msg[500];
            sprintf(msg,"received '%d' dimensional array instead of '%d' dimensional array for variable '%s'",
                    arr_obj->nd,Ndims,name);
            throw_error(PyExc_TypeError,msg);
        }
    }
};

numpy_size_handler x__numpy_size_handler = numpy_size_handler();
#define conversion_numpy_check_size x__numpy_size_handler.conversion_numpy_check_size
#define numpy_check_size x__numpy_size_handler.numpy_check_size


class numpy_type_handler
{
public:
    void conversion_numpy_check_type(PyArrayObject* arr_obj, int numeric_type,
                                     const char* name)
    {
        // Make sure input has correct numeric type.
        int arr_type = arr_obj->descr->type_num;
        if (PyTypeNum_ISEXTENDED(numeric_type))
        {
        char msg[80];
        sprintf(msg, "Conversion Error: extended types not supported for variable '%s'",
                name);
        throw_error(PyExc_TypeError, msg);
        }
        if (!PyArray_EquivTypenums(arr_type, numeric_type))
        {

        const char* type_names[23] = {"bool", "byte", "ubyte","short", "ushort",
                                "int", "uint", "long", "ulong", "longlong", "ulonglong",
                                "float", "double", "longdouble", "cfloat", "cdouble",
                                "clongdouble", "object", "string", "unicode", "void", "ntype",
                                "unknown"};
        char msg[500];
        sprintf(msg,"Conversion Error: received '%s' typed array instead of '%s' typed array for variable '%s'",
                type_names[arr_type],type_names[numeric_type],name);
        throw_error(PyExc_TypeError,msg);
        }
    }

    void numpy_check_type(PyArrayObject* arr_obj, int numeric_type, const char* name)
    {
        // Make sure input has correct numeric type.
        int arr_type = arr_obj->descr->type_num;
        if (PyTypeNum_ISEXTENDED(numeric_type))
        {
        char msg[80];
        sprintf(msg, "Conversion Error: extended types not supported for variable '%s'",
                name);
        throw_error(PyExc_TypeError, msg);
        }
        if (!PyArray_EquivTypenums(arr_type, numeric_type))
        {
            const char* type_names[23] = {"bool", "byte", "ubyte","short", "ushort",
                                    "int", "uint", "long", "ulong", "longlong", "ulonglong",
                                    "float", "double", "longdouble", "cfloat", "cdouble",
                                    "clongdouble", "object", "string", "unicode", "void", "ntype",
                                    "unknown"};
            char msg[500];
            sprintf(msg,"received '%s' typed array instead of '%s' typed array for variable '%s'",
                    type_names[arr_type],type_names[numeric_type],name);
            throw_error(PyExc_TypeError,msg);
        }
    }
};

numpy_type_handler x__numpy_type_handler = numpy_type_handler();
#define conversion_numpy_check_type x__numpy_type_handler.conversion_numpy_check_type
#define numpy_check_type x__numpy_type_handler.numpy_check_type


class numpy_handler
{
public:
    PyArrayObject* convert_to_numpy(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        Py_XINCREF(py_obj);
        if (!py_obj || !PyArray_Check(py_obj))
            handle_conversion_error(py_obj,"numpy", name);
        return (PyArrayObject*) py_obj;
    }

    PyArrayObject* py_to_numpy(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !PyArray_Check(py_obj))
            handle_bad_type(py_obj,"numpy", name);
        Py_XINCREF(py_obj);
        return (PyArrayObject*) py_obj;
    }
};

numpy_handler x__numpy_handler = numpy_handler();
#define convert_to_numpy(py_obj,name) \
        x__numpy_handler.convert_to_numpy(py_obj,name)
#define py_to_numpy(py_obj,name) \
        x__numpy_handler.py_to_numpy(py_obj,name)


PyObject* numpy_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


class catchall_handler
{
public:
    py::object convert_to_catchall(PyObject* py_obj, const char* name)
    {
        // Incref occurs even if conversion fails so that
        // the decref in cleanup_code has a matching incref.
        
        if (!py_obj || !(py_obj))
            handle_conversion_error(py_obj,"catchall", name);
        return py::object(py_obj);
    }

    py::object py_to_catchall(PyObject* py_obj, const char* name)
    {
        // !! Pretty sure INCREF should only be called on success since
        // !! py_to_xxx is used by the user -- not the code generator.
        if (!py_obj || !(py_obj))
            handle_bad_type(py_obj,"catchall", name);
        
        return py::object(py_obj);
    }
};

catchall_handler x__catchall_handler = catchall_handler();
#define convert_to_catchall(py_obj,name) \
        x__catchall_handler.convert_to_catchall(py_obj,name)
#define py_to_catchall(py_obj,name) \
        x__catchall_handler.py_to_catchall(py_obj,name)


PyObject* catchall_to_py(PyObject* obj)
{
    return (PyObject*) obj;
}


    int cellType(int cellId, int* cutoff) {
        if (cellId > cutoff[1]) {
            return 2;
        } else if (cellId < cutoff[0]) {
            return 0;
        } else {
            return 1;
        }
    }
    
    double fb_dist(double x1, double y1, double x2, double y2) {
        double r = sqrt(pow((x1-x2),2) + pow((y1-y2),2));
        return r;
    }
    
    double fb_fitInto(double v, double upper) {
        if (v > upper) {
            return upper;
        } else if (v < 0.) {
            return 0.;
        } else {
            return v;
        }
    }
    
    double pb_dist(double x1, double x2, double size_x) {
        double x = x2-x1;
        if (x > size_x/2.){
        x -= size_x;
        } else if (x < -size_x/2.){
        x += size_x;
        }

        return x;
    }
    
    double pb_fitInto(double v, double upper) {
        if (v >= upper) {
            return v-upper;
        } else if (v < 0.) {
            return v+upper;
        } else {
            return v;
        }
    }
    

static PyObject* fb_tick(PyObject*self, PyObject* args, PyObject* kywds)
{
    py::object return_val;
    int exception_occurred = 0;
    PyObject *py_local_dict = NULL;
    static const char *kwlist[] = {"n","size_x","size_y","r0","r1","rv","inert","f0","fa","nint","v0","pinned","cutoff","beta","grad_x","grad_y","pos_x","pos_y","v_x","v_y","local_dict", NULL};
    PyObject *py_n, *py_size_x, *py_size_y, *py_r0, *py_r1, *py_rv, *py_inert, *py_f0, *py_fa, *py_nint, *py_v0, *py_pinned, *py_cutoff, *py_beta, *py_grad_x, *py_grad_y, *py_pos_x, *py_pos_y, *py_v_x, *py_v_y;
    int n_used, size_x_used, size_y_used, r0_used, r1_used, rv_used, inert_used, f0_used, fa_used, nint_used, v0_used, pinned_used, cutoff_used, beta_used, grad_x_used, grad_y_used, pos_x_used, pos_y_used, v_x_used, v_y_used;
    py_n = py_size_x = py_size_y = py_r0 = py_r1 = py_rv = py_inert = py_f0 = py_fa = py_nint = py_v0 = py_pinned = py_cutoff = py_beta = py_grad_x = py_grad_y = py_pos_x = py_pos_y = py_v_x = py_v_y = NULL;
    n_used= size_x_used= size_y_used= r0_used= r1_used= rv_used= inert_used= f0_used= fa_used= nint_used= v0_used= pinned_used= cutoff_used= beta_used= grad_x_used= grad_y_used= pos_x_used= pos_y_used= v_x_used= v_y_used = 0;
    
    if(!PyArg_ParseTupleAndKeywords(args,kywds,"OOOOOOOOOOOOOOOOOOOO|O:fb_tick",const_cast<char**>(kwlist),&py_n, &py_size_x, &py_size_y, &py_r0, &py_r1, &py_rv, &py_inert, &py_f0, &py_fa, &py_nint, &py_v0, &py_pinned, &py_cutoff, &py_beta, &py_grad_x, &py_grad_y, &py_pos_x, &py_pos_y, &py_v_x, &py_v_y, &py_local_dict))
       return NULL;
    try                              
    {                                
        py_n = py_n;
        int n = convert_to_int(py_n,"n");
        n_used = 1;
        py_size_x = py_size_x;
        double size_x = convert_to_float(py_size_x,"size_x");
        size_x_used = 1;
        py_size_y = py_size_y;
        double size_y = convert_to_float(py_size_y,"size_y");
        size_y_used = 1;
        py_r0 = py_r0;
        double r0 = convert_to_float(py_r0,"r0");
        r0_used = 1;
        py_r1 = py_r1;
        double r1 = convert_to_float(py_r1,"r1");
        r1_used = 1;
        py_rv = py_rv;
        double rv = convert_to_float(py_rv,"rv");
        rv_used = 1;
        py_inert = py_inert;
        double inert = convert_to_float(py_inert,"inert");
        inert_used = 1;
        py_f0 = py_f0;
        double f0 = convert_to_float(py_f0,"f0");
        f0_used = 1;
        py_fa = py_fa;
        double fa = convert_to_float(py_fa,"fa");
        fa_used = 1;
        py_nint = py_nint;
        double nint = convert_to_float(py_nint,"nint");
        nint_used = 1;
        py_v0 = py_v0;
        PyArrayObject* v0_array = convert_to_numpy(py_v0,"v0");
        conversion_numpy_check_type(v0_array,PyArray_DOUBLE,"v0");
        #define V01(i) (*((double*)(v0_array->data + (i)*Sv0[0])))
        #define V02(i,j) (*((double*)(v0_array->data + (i)*Sv0[0] + (j)*Sv0[1])))
        #define V03(i,j,k) (*((double*)(v0_array->data + (i)*Sv0[0] + (j)*Sv0[1] + (k)*Sv0[2])))
        #define V04(i,j,k,l) (*((double*)(v0_array->data + (i)*Sv0[0] + (j)*Sv0[1] + (k)*Sv0[2] + (l)*Sv0[3])))
        npy_intp* Nv0 = v0_array->dimensions;
        npy_intp* Sv0 = v0_array->strides;
        int Dv0 = v0_array->nd;
        double* v0 = (double*) v0_array->data;
        v0_used = 1;
        py_pinned = py_pinned;
        PyArrayObject* pinned_array = convert_to_numpy(py_pinned,"pinned");
        conversion_numpy_check_type(pinned_array,PyArray_INT,"pinned");
        #define PINNED1(i) (*((int*)(pinned_array->data + (i)*Spinned[0])))
        #define PINNED2(i,j) (*((int*)(pinned_array->data + (i)*Spinned[0] + (j)*Spinned[1])))
        #define PINNED3(i,j,k) (*((int*)(pinned_array->data + (i)*Spinned[0] + (j)*Spinned[1] + (k)*Spinned[2])))
        #define PINNED4(i,j,k,l) (*((int*)(pinned_array->data + (i)*Spinned[0] + (j)*Spinned[1] + (k)*Spinned[2] + (l)*Spinned[3])))
        npy_intp* Npinned = pinned_array->dimensions;
        npy_intp* Spinned = pinned_array->strides;
        int Dpinned = pinned_array->nd;
        int* pinned = (int*) pinned_array->data;
        pinned_used = 1;
        py_cutoff = py_cutoff;
        PyArrayObject* cutoff_array = convert_to_numpy(py_cutoff,"cutoff");
        conversion_numpy_check_type(cutoff_array,PyArray_INT,"cutoff");
        #define CUTOFF1(i) (*((int*)(cutoff_array->data + (i)*Scutoff[0])))
        #define CUTOFF2(i,j) (*((int*)(cutoff_array->data + (i)*Scutoff[0] + (j)*Scutoff[1])))
        #define CUTOFF3(i,j,k) (*((int*)(cutoff_array->data + (i)*Scutoff[0] + (j)*Scutoff[1] + (k)*Scutoff[2])))
        #define CUTOFF4(i,j,k,l) (*((int*)(cutoff_array->data + (i)*Scutoff[0] + (j)*Scutoff[1] + (k)*Scutoff[2] + (l)*Scutoff[3])))
        npy_intp* Ncutoff = cutoff_array->dimensions;
        npy_intp* Scutoff = cutoff_array->strides;
        int Dcutoff = cutoff_array->nd;
        int* cutoff = (int*) cutoff_array->data;
        cutoff_used = 1;
        py_beta = py_beta;
        PyArrayObject* beta_array = convert_to_numpy(py_beta,"beta");
        conversion_numpy_check_type(beta_array,PyArray_DOUBLE,"beta");
        #define BETA1(i) (*((double*)(beta_array->data + (i)*Sbeta[0])))
        #define BETA2(i,j) (*((double*)(beta_array->data + (i)*Sbeta[0] + (j)*Sbeta[1])))
        #define BETA3(i,j,k) (*((double*)(beta_array->data + (i)*Sbeta[0] + (j)*Sbeta[1] + (k)*Sbeta[2])))
        #define BETA4(i,j,k,l) (*((double*)(beta_array->data + (i)*Sbeta[0] + (j)*Sbeta[1] + (k)*Sbeta[2] + (l)*Sbeta[3])))
        npy_intp* Nbeta = beta_array->dimensions;
        npy_intp* Sbeta = beta_array->strides;
        int Dbeta = beta_array->nd;
        double* beta = (double*) beta_array->data;
        beta_used = 1;
        py_grad_x = py_grad_x;
        PyArrayObject* grad_x_array = convert_to_numpy(py_grad_x,"grad_x");
        conversion_numpy_check_type(grad_x_array,PyArray_DOUBLE,"grad_x");
        #define GRAD_X1(i) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0])))
        #define GRAD_X2(i,j) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0] + (j)*Sgrad_x[1])))
        #define GRAD_X3(i,j,k) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0] + (j)*Sgrad_x[1] + (k)*Sgrad_x[2])))
        #define GRAD_X4(i,j,k,l) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0] + (j)*Sgrad_x[1] + (k)*Sgrad_x[2] + (l)*Sgrad_x[3])))
        npy_intp* Ngrad_x = grad_x_array->dimensions;
        npy_intp* Sgrad_x = grad_x_array->strides;
        int Dgrad_x = grad_x_array->nd;
        double* grad_x = (double*) grad_x_array->data;
        grad_x_used = 1;
        py_grad_y = py_grad_y;
        PyArrayObject* grad_y_array = convert_to_numpy(py_grad_y,"grad_y");
        conversion_numpy_check_type(grad_y_array,PyArray_DOUBLE,"grad_y");
        #define GRAD_Y1(i) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0])))
        #define GRAD_Y2(i,j) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0] + (j)*Sgrad_y[1])))
        #define GRAD_Y3(i,j,k) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0] + (j)*Sgrad_y[1] + (k)*Sgrad_y[2])))
        #define GRAD_Y4(i,j,k,l) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0] + (j)*Sgrad_y[1] + (k)*Sgrad_y[2] + (l)*Sgrad_y[3])))
        npy_intp* Ngrad_y = grad_y_array->dimensions;
        npy_intp* Sgrad_y = grad_y_array->strides;
        int Dgrad_y = grad_y_array->nd;
        double* grad_y = (double*) grad_y_array->data;
        grad_y_used = 1;
        py_pos_x = py_pos_x;
        PyArrayObject* pos_x_array = convert_to_numpy(py_pos_x,"pos_x");
        conversion_numpy_check_type(pos_x_array,PyArray_DOUBLE,"pos_x");
        #define POS_X1(i) (*((double*)(pos_x_array->data + (i)*Spos_x[0])))
        #define POS_X2(i,j) (*((double*)(pos_x_array->data + (i)*Spos_x[0] + (j)*Spos_x[1])))
        #define POS_X3(i,j,k) (*((double*)(pos_x_array->data + (i)*Spos_x[0] + (j)*Spos_x[1] + (k)*Spos_x[2])))
        #define POS_X4(i,j,k,l) (*((double*)(pos_x_array->data + (i)*Spos_x[0] + (j)*Spos_x[1] + (k)*Spos_x[2] + (l)*Spos_x[3])))
        npy_intp* Npos_x = pos_x_array->dimensions;
        npy_intp* Spos_x = pos_x_array->strides;
        int Dpos_x = pos_x_array->nd;
        double* pos_x = (double*) pos_x_array->data;
        pos_x_used = 1;
        py_pos_y = py_pos_y;
        PyArrayObject* pos_y_array = convert_to_numpy(py_pos_y,"pos_y");
        conversion_numpy_check_type(pos_y_array,PyArray_DOUBLE,"pos_y");
        #define POS_Y1(i) (*((double*)(pos_y_array->data + (i)*Spos_y[0])))
        #define POS_Y2(i,j) (*((double*)(pos_y_array->data + (i)*Spos_y[0] + (j)*Spos_y[1])))
        #define POS_Y3(i,j,k) (*((double*)(pos_y_array->data + (i)*Spos_y[0] + (j)*Spos_y[1] + (k)*Spos_y[2])))
        #define POS_Y4(i,j,k,l) (*((double*)(pos_y_array->data + (i)*Spos_y[0] + (j)*Spos_y[1] + (k)*Spos_y[2] + (l)*Spos_y[3])))
        npy_intp* Npos_y = pos_y_array->dimensions;
        npy_intp* Spos_y = pos_y_array->strides;
        int Dpos_y = pos_y_array->nd;
        double* pos_y = (double*) pos_y_array->data;
        pos_y_used = 1;
        py_v_x = py_v_x;
        PyArrayObject* v_x_array = convert_to_numpy(py_v_x,"v_x");
        conversion_numpy_check_type(v_x_array,PyArray_DOUBLE,"v_x");
        #define V_X1(i) (*((double*)(v_x_array->data + (i)*Sv_x[0])))
        #define V_X2(i,j) (*((double*)(v_x_array->data + (i)*Sv_x[0] + (j)*Sv_x[1])))
        #define V_X3(i,j,k) (*((double*)(v_x_array->data + (i)*Sv_x[0] + (j)*Sv_x[1] + (k)*Sv_x[2])))
        #define V_X4(i,j,k,l) (*((double*)(v_x_array->data + (i)*Sv_x[0] + (j)*Sv_x[1] + (k)*Sv_x[2] + (l)*Sv_x[3])))
        npy_intp* Nv_x = v_x_array->dimensions;
        npy_intp* Sv_x = v_x_array->strides;
        int Dv_x = v_x_array->nd;
        double* v_x = (double*) v_x_array->data;
        v_x_used = 1;
        py_v_y = py_v_y;
        PyArrayObject* v_y_array = convert_to_numpy(py_v_y,"v_y");
        conversion_numpy_check_type(v_y_array,PyArray_DOUBLE,"v_y");
        #define V_Y1(i) (*((double*)(v_y_array->data + (i)*Sv_y[0])))
        #define V_Y2(i,j) (*((double*)(v_y_array->data + (i)*Sv_y[0] + (j)*Sv_y[1])))
        #define V_Y3(i,j,k) (*((double*)(v_y_array->data + (i)*Sv_y[0] + (j)*Sv_y[1] + (k)*Sv_y[2])))
        #define V_Y4(i,j,k,l) (*((double*)(v_y_array->data + (i)*Sv_y[0] + (j)*Sv_y[1] + (k)*Sv_y[2] + (l)*Sv_y[3])))
        npy_intp* Nv_y = v_y_array->dimensions;
        npy_intp* Sv_y = v_y_array->strides;
        int Dv_y = v_y_array->nd;
        double* v_y = (double*) v_y_array->data;
        v_y_used = 1;
        /*<function call here>*/     
        
            int i;
            int j;
            int ctype;
            double r;
            double temp;
            double noise;
            double c;
            double s;
            double f_x;
            double f_y;
            double avgdir_x;
            double avgdir_y;
            int inf_count;
        
            for (i = 0; i < n; i++)
            {
                ctype = cellType(i, cutoff);
                if (pinned[ctype] == 0) {
                    // Initiate Attraction-Repulsion Strengths
                    f_x = 0;
                    f_y = 0;
                    inf_count = 0;
                    // Initiate Alignment Strengths
                    avgdir_x = 0;
                    avgdir_y = 0;
        
                    for (j = 0; j < n; j++)
                    {
                        r = fb_dist(pos_x[i], pos_y[i], pos_x[j], pos_y[j]);
                        //Attraction-Repulsion Strength
                        if (i != j) {
                            if (r <= r1) {
                                if (r < r0) {
                                    //Infinite repulsion
                                    if (inf_count == 0) {
                                        f_x = 0;
                                        f_y = 0;
                                    }
                                    inf_count++;
                                    if (r > 0) {//Avoid dividing by zero
                                        f_x += (pos_x[i]-pos_x[j])/r;
                                        f_y += (pos_y[i]-pos_y[j])/r;
                                    }
                                } else {
                                    //Equilibrium attraction and repulsion
                                    if (inf_count == 0){
                                        temp = -f0 + (r-r0)/(r1-r0)*(1+beta[ctype*3+cellType(j, cutoff)])*f0;
                                        f_x += temp*(pos_x[j]-pos_x[i])/r;
                                        f_y += temp*(pos_y[j]-pos_y[i])/r;
                                    }
                                }
                            }
                        }
                        //Alignment Strength
                        if (r <= rv) {
                            temp = sqrt(pow(v_x[j],2) + pow(v_y[j],2));
                            if (temp > 0) {
                                avgdir_x += v_x[j]/temp;
                                avgdir_y += v_y[j]/temp;
                            }
                        }
                    }
        
                    // ANGULAR INERTIA
                    v_x[i] *= inert;
                    v_y[i] *= inert;
        
                    // INTERACTION
                    if (inf_count > 0) {
                        f_x = f_x/inf_count*10000;
                        f_y = f_y/inf_count*10000;
                    }
                    v_x[i] += f_x;
                    v_y[i] += f_y;
        
                    // ALIGNMENT
                    temp = sqrt(pow(avgdir_x,2) + pow(avgdir_y,2));
                    if (temp > 0) {//Avoid dividing by zero
                        avgdir_x /= temp;
                        avgdir_y /= temp;
                    }
                    v_x[i] += fa * avgdir_x;
                    v_y[i] += fa * avgdir_y;
        
                    //GRADIENT
                    v_x[i] += grad_x[ctype];
                    v_y[i] += grad_y[ctype];
        
                    //NORMALIZE into unit vector (contain angle info)
                    temp = sqrt(pow(v_x[i],2) + pow(v_y[i],2));
                    if (temp > 0) {//Avoid dividing by zero
                        v_x[i] /= temp;
                        v_y[i] /= temp;
                    }
        
                    //NOISE
                    noise = nint*M_PI*((static_cast <float> (rand()) / static_cast <float> (RAND_MAX))*2-1);
                    c = cos(noise);
                    s = sin(noise);
                    temp = v_x[i];
                    v_x[i] = v0[ctype]*(v_x[i]*c - v_y[i]*s);
                    v_y[i] = v0[ctype]*(temp*s + v_y[i]*c);
                }
            }
        
            for (i = 0; i < n; i++)
            {
                ctype = cellType(i, cutoff);
                if (pinned[ctype] == 0) {
                    //WITHIN BOUNDARY
                    pos_x[i] += v_x[i];
                    pos_x[i] = fb_fitInto(pos_x[i], size_x);
                    pos_y[i] += v_y[i];
                    pos_y[i] = fb_fitInto(pos_y[i], size_y);
                }
            }
        
        if(py_local_dict)                                  
        {                                                  
            py::dict local_dict = py::dict(py_local_dict); 
        }                                                  
    
    }                                
    catch(...)                       
    {                                
        return_val =  py::object();      
        exception_occurred = 1;       
    }                                
    /*cleanup code*/                     
    if(v0_used)
    {
        Py_XDECREF(py_v0);
        #undef V01
        #undef V02
        #undef V03
        #undef V04
    }
    if(pinned_used)
    {
        Py_XDECREF(py_pinned);
        #undef PINNED1
        #undef PINNED2
        #undef PINNED3
        #undef PINNED4
    }
    if(cutoff_used)
    {
        Py_XDECREF(py_cutoff);
        #undef CUTOFF1
        #undef CUTOFF2
        #undef CUTOFF3
        #undef CUTOFF4
    }
    if(beta_used)
    {
        Py_XDECREF(py_beta);
        #undef BETA1
        #undef BETA2
        #undef BETA3
        #undef BETA4
    }
    if(grad_x_used)
    {
        Py_XDECREF(py_grad_x);
        #undef GRAD_X1
        #undef GRAD_X2
        #undef GRAD_X3
        #undef GRAD_X4
    }
    if(grad_y_used)
    {
        Py_XDECREF(py_grad_y);
        #undef GRAD_Y1
        #undef GRAD_Y2
        #undef GRAD_Y3
        #undef GRAD_Y4
    }
    if(pos_x_used)
    {
        Py_XDECREF(py_pos_x);
        #undef POS_X1
        #undef POS_X2
        #undef POS_X3
        #undef POS_X4
    }
    if(pos_y_used)
    {
        Py_XDECREF(py_pos_y);
        #undef POS_Y1
        #undef POS_Y2
        #undef POS_Y3
        #undef POS_Y4
    }
    if(v_x_used)
    {
        Py_XDECREF(py_v_x);
        #undef V_X1
        #undef V_X2
        #undef V_X3
        #undef V_X4
    }
    if(v_y_used)
    {
        Py_XDECREF(py_v_y);
        #undef V_Y1
        #undef V_Y2
        #undef V_Y3
        #undef V_Y4
    }
    if(!(PyObject*)return_val && !exception_occurred)
    {
                                  
        return_val = Py_None;            
    }
                                  
    return return_val.disown();           
}                                
static PyObject* pb_tick(PyObject*self, PyObject* args, PyObject* kywds)
{
    py::object return_val;
    int exception_occurred = 0;
    PyObject *py_local_dict = NULL;
    static const char *kwlist[] = {"n","size_x","size_y","r0","r1","rv","inert","f0","fa","nint","v0","pinned","cutoff","beta","grad_x","grad_y","pos_x","pos_y","v_x","v_y","local_dict", NULL};
    PyObject *py_n, *py_size_x, *py_size_y, *py_r0, *py_r1, *py_rv, *py_inert, *py_f0, *py_fa, *py_nint, *py_v0, *py_pinned, *py_cutoff, *py_beta, *py_grad_x, *py_grad_y, *py_pos_x, *py_pos_y, *py_v_x, *py_v_y;
    int n_used, size_x_used, size_y_used, r0_used, r1_used, rv_used, inert_used, f0_used, fa_used, nint_used, v0_used, pinned_used, cutoff_used, beta_used, grad_x_used, grad_y_used, pos_x_used, pos_y_used, v_x_used, v_y_used;
    py_n = py_size_x = py_size_y = py_r0 = py_r1 = py_rv = py_inert = py_f0 = py_fa = py_nint = py_v0 = py_pinned = py_cutoff = py_beta = py_grad_x = py_grad_y = py_pos_x = py_pos_y = py_v_x = py_v_y = NULL;
    n_used= size_x_used= size_y_used= r0_used= r1_used= rv_used= inert_used= f0_used= fa_used= nint_used= v0_used= pinned_used= cutoff_used= beta_used= grad_x_used= grad_y_used= pos_x_used= pos_y_used= v_x_used= v_y_used = 0;
    
    if(!PyArg_ParseTupleAndKeywords(args,kywds,"OOOOOOOOOOOOOOOOOOOO|O:pb_tick",const_cast<char**>(kwlist),&py_n, &py_size_x, &py_size_y, &py_r0, &py_r1, &py_rv, &py_inert, &py_f0, &py_fa, &py_nint, &py_v0, &py_pinned, &py_cutoff, &py_beta, &py_grad_x, &py_grad_y, &py_pos_x, &py_pos_y, &py_v_x, &py_v_y, &py_local_dict))
       return NULL;
    try                              
    {                                
        py_n = py_n;
        int n = convert_to_int(py_n,"n");
        n_used = 1;
        py_size_x = py_size_x;
        double size_x = convert_to_float(py_size_x,"size_x");
        size_x_used = 1;
        py_size_y = py_size_y;
        double size_y = convert_to_float(py_size_y,"size_y");
        size_y_used = 1;
        py_r0 = py_r0;
        double r0 = convert_to_float(py_r0,"r0");
        r0_used = 1;
        py_r1 = py_r1;
        double r1 = convert_to_float(py_r1,"r1");
        r1_used = 1;
        py_rv = py_rv;
        double rv = convert_to_float(py_rv,"rv");
        rv_used = 1;
        py_inert = py_inert;
        double inert = convert_to_float(py_inert,"inert");
        inert_used = 1;
        py_f0 = py_f0;
        double f0 = convert_to_float(py_f0,"f0");
        f0_used = 1;
        py_fa = py_fa;
        double fa = convert_to_float(py_fa,"fa");
        fa_used = 1;
        py_nint = py_nint;
        double nint = convert_to_float(py_nint,"nint");
        nint_used = 1;
        py_v0 = py_v0;
        PyArrayObject* v0_array = convert_to_numpy(py_v0,"v0");
        conversion_numpy_check_type(v0_array,PyArray_DOUBLE,"v0");
        #define V01(i) (*((double*)(v0_array->data + (i)*Sv0[0])))
        #define V02(i,j) (*((double*)(v0_array->data + (i)*Sv0[0] + (j)*Sv0[1])))
        #define V03(i,j,k) (*((double*)(v0_array->data + (i)*Sv0[0] + (j)*Sv0[1] + (k)*Sv0[2])))
        #define V04(i,j,k,l) (*((double*)(v0_array->data + (i)*Sv0[0] + (j)*Sv0[1] + (k)*Sv0[2] + (l)*Sv0[3])))
        npy_intp* Nv0 = v0_array->dimensions;
        npy_intp* Sv0 = v0_array->strides;
        int Dv0 = v0_array->nd;
        double* v0 = (double*) v0_array->data;
        v0_used = 1;
        py_pinned = py_pinned;
        PyArrayObject* pinned_array = convert_to_numpy(py_pinned,"pinned");
        conversion_numpy_check_type(pinned_array,PyArray_INT,"pinned");
        #define PINNED1(i) (*((int*)(pinned_array->data + (i)*Spinned[0])))
        #define PINNED2(i,j) (*((int*)(pinned_array->data + (i)*Spinned[0] + (j)*Spinned[1])))
        #define PINNED3(i,j,k) (*((int*)(pinned_array->data + (i)*Spinned[0] + (j)*Spinned[1] + (k)*Spinned[2])))
        #define PINNED4(i,j,k,l) (*((int*)(pinned_array->data + (i)*Spinned[0] + (j)*Spinned[1] + (k)*Spinned[2] + (l)*Spinned[3])))
        npy_intp* Npinned = pinned_array->dimensions;
        npy_intp* Spinned = pinned_array->strides;
        int Dpinned = pinned_array->nd;
        int* pinned = (int*) pinned_array->data;
        pinned_used = 1;
        py_cutoff = py_cutoff;
        PyArrayObject* cutoff_array = convert_to_numpy(py_cutoff,"cutoff");
        conversion_numpy_check_type(cutoff_array,PyArray_INT,"cutoff");
        #define CUTOFF1(i) (*((int*)(cutoff_array->data + (i)*Scutoff[0])))
        #define CUTOFF2(i,j) (*((int*)(cutoff_array->data + (i)*Scutoff[0] + (j)*Scutoff[1])))
        #define CUTOFF3(i,j,k) (*((int*)(cutoff_array->data + (i)*Scutoff[0] + (j)*Scutoff[1] + (k)*Scutoff[2])))
        #define CUTOFF4(i,j,k,l) (*((int*)(cutoff_array->data + (i)*Scutoff[0] + (j)*Scutoff[1] + (k)*Scutoff[2] + (l)*Scutoff[3])))
        npy_intp* Ncutoff = cutoff_array->dimensions;
        npy_intp* Scutoff = cutoff_array->strides;
        int Dcutoff = cutoff_array->nd;
        int* cutoff = (int*) cutoff_array->data;
        cutoff_used = 1;
        py_beta = py_beta;
        PyArrayObject* beta_array = convert_to_numpy(py_beta,"beta");
        conversion_numpy_check_type(beta_array,PyArray_DOUBLE,"beta");
        #define BETA1(i) (*((double*)(beta_array->data + (i)*Sbeta[0])))
        #define BETA2(i,j) (*((double*)(beta_array->data + (i)*Sbeta[0] + (j)*Sbeta[1])))
        #define BETA3(i,j,k) (*((double*)(beta_array->data + (i)*Sbeta[0] + (j)*Sbeta[1] + (k)*Sbeta[2])))
        #define BETA4(i,j,k,l) (*((double*)(beta_array->data + (i)*Sbeta[0] + (j)*Sbeta[1] + (k)*Sbeta[2] + (l)*Sbeta[3])))
        npy_intp* Nbeta = beta_array->dimensions;
        npy_intp* Sbeta = beta_array->strides;
        int Dbeta = beta_array->nd;
        double* beta = (double*) beta_array->data;
        beta_used = 1;
        py_grad_x = py_grad_x;
        PyArrayObject* grad_x_array = convert_to_numpy(py_grad_x,"grad_x");
        conversion_numpy_check_type(grad_x_array,PyArray_DOUBLE,"grad_x");
        #define GRAD_X1(i) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0])))
        #define GRAD_X2(i,j) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0] + (j)*Sgrad_x[1])))
        #define GRAD_X3(i,j,k) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0] + (j)*Sgrad_x[1] + (k)*Sgrad_x[2])))
        #define GRAD_X4(i,j,k,l) (*((double*)(grad_x_array->data + (i)*Sgrad_x[0] + (j)*Sgrad_x[1] + (k)*Sgrad_x[2] + (l)*Sgrad_x[3])))
        npy_intp* Ngrad_x = grad_x_array->dimensions;
        npy_intp* Sgrad_x = grad_x_array->strides;
        int Dgrad_x = grad_x_array->nd;
        double* grad_x = (double*) grad_x_array->data;
        grad_x_used = 1;
        py_grad_y = py_grad_y;
        PyArrayObject* grad_y_array = convert_to_numpy(py_grad_y,"grad_y");
        conversion_numpy_check_type(grad_y_array,PyArray_DOUBLE,"grad_y");
        #define GRAD_Y1(i) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0])))
        #define GRAD_Y2(i,j) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0] + (j)*Sgrad_y[1])))
        #define GRAD_Y3(i,j,k) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0] + (j)*Sgrad_y[1] + (k)*Sgrad_y[2])))
        #define GRAD_Y4(i,j,k,l) (*((double*)(grad_y_array->data + (i)*Sgrad_y[0] + (j)*Sgrad_y[1] + (k)*Sgrad_y[2] + (l)*Sgrad_y[3])))
        npy_intp* Ngrad_y = grad_y_array->dimensions;
        npy_intp* Sgrad_y = grad_y_array->strides;
        int Dgrad_y = grad_y_array->nd;
        double* grad_y = (double*) grad_y_array->data;
        grad_y_used = 1;
        py_pos_x = py_pos_x;
        PyArrayObject* pos_x_array = convert_to_numpy(py_pos_x,"pos_x");
        conversion_numpy_check_type(pos_x_array,PyArray_DOUBLE,"pos_x");
        #define POS_X1(i) (*((double*)(pos_x_array->data + (i)*Spos_x[0])))
        #define POS_X2(i,j) (*((double*)(pos_x_array->data + (i)*Spos_x[0] + (j)*Spos_x[1])))
        #define POS_X3(i,j,k) (*((double*)(pos_x_array->data + (i)*Spos_x[0] + (j)*Spos_x[1] + (k)*Spos_x[2])))
        #define POS_X4(i,j,k,l) (*((double*)(pos_x_array->data + (i)*Spos_x[0] + (j)*Spos_x[1] + (k)*Spos_x[2] + (l)*Spos_x[3])))
        npy_intp* Npos_x = pos_x_array->dimensions;
        npy_intp* Spos_x = pos_x_array->strides;
        int Dpos_x = pos_x_array->nd;
        double* pos_x = (double*) pos_x_array->data;
        pos_x_used = 1;
        py_pos_y = py_pos_y;
        PyArrayObject* pos_y_array = convert_to_numpy(py_pos_y,"pos_y");
        conversion_numpy_check_type(pos_y_array,PyArray_DOUBLE,"pos_y");
        #define POS_Y1(i) (*((double*)(pos_y_array->data + (i)*Spos_y[0])))
        #define POS_Y2(i,j) (*((double*)(pos_y_array->data + (i)*Spos_y[0] + (j)*Spos_y[1])))
        #define POS_Y3(i,j,k) (*((double*)(pos_y_array->data + (i)*Spos_y[0] + (j)*Spos_y[1] + (k)*Spos_y[2])))
        #define POS_Y4(i,j,k,l) (*((double*)(pos_y_array->data + (i)*Spos_y[0] + (j)*Spos_y[1] + (k)*Spos_y[2] + (l)*Spos_y[3])))
        npy_intp* Npos_y = pos_y_array->dimensions;
        npy_intp* Spos_y = pos_y_array->strides;
        int Dpos_y = pos_y_array->nd;
        double* pos_y = (double*) pos_y_array->data;
        pos_y_used = 1;
        py_v_x = py_v_x;
        PyArrayObject* v_x_array = convert_to_numpy(py_v_x,"v_x");
        conversion_numpy_check_type(v_x_array,PyArray_DOUBLE,"v_x");
        #define V_X1(i) (*((double*)(v_x_array->data + (i)*Sv_x[0])))
        #define V_X2(i,j) (*((double*)(v_x_array->data + (i)*Sv_x[0] + (j)*Sv_x[1])))
        #define V_X3(i,j,k) (*((double*)(v_x_array->data + (i)*Sv_x[0] + (j)*Sv_x[1] + (k)*Sv_x[2])))
        #define V_X4(i,j,k,l) (*((double*)(v_x_array->data + (i)*Sv_x[0] + (j)*Sv_x[1] + (k)*Sv_x[2] + (l)*Sv_x[3])))
        npy_intp* Nv_x = v_x_array->dimensions;
        npy_intp* Sv_x = v_x_array->strides;
        int Dv_x = v_x_array->nd;
        double* v_x = (double*) v_x_array->data;
        v_x_used = 1;
        py_v_y = py_v_y;
        PyArrayObject* v_y_array = convert_to_numpy(py_v_y,"v_y");
        conversion_numpy_check_type(v_y_array,PyArray_DOUBLE,"v_y");
        #define V_Y1(i) (*((double*)(v_y_array->data + (i)*Sv_y[0])))
        #define V_Y2(i,j) (*((double*)(v_y_array->data + (i)*Sv_y[0] + (j)*Sv_y[1])))
        #define V_Y3(i,j,k) (*((double*)(v_y_array->data + (i)*Sv_y[0] + (j)*Sv_y[1] + (k)*Sv_y[2])))
        #define V_Y4(i,j,k,l) (*((double*)(v_y_array->data + (i)*Sv_y[0] + (j)*Sv_y[1] + (k)*Sv_y[2] + (l)*Sv_y[3])))
        npy_intp* Nv_y = v_y_array->dimensions;
        npy_intp* Sv_y = v_y_array->strides;
        int Dv_y = v_y_array->nd;
        double* v_y = (double*) v_y_array->data;
        v_y_used = 1;
        /*<function call here>*/     
        
            int i;
            int j;
            int ctype;
            double r;
            double temp;
            double noise;
            double c;
            double s;
            double f_x;
            double f_y;
            double dis_x;
            double dis_y;
            double avgdir_x;
            double avgdir_y;
            int inf_count;
        
            for (i = 0; i < n; i++)
            {
                ctype = cellType(i, cutoff);
                if (pinned[ctype] == 0) {
                    // Initiate Attraction-Repulsion Strengths
                    f_x = 0;
                    f_y = 0;
                    inf_count = 0;
                    // Initiate Alignment Strengths
                    avgdir_x = 0;
                    avgdir_y = 0;
        
                    for (j = 0; j < n; j++)
                    {
                        dis_x = pb_dist(pos_x[i], pos_x[j], size_x);
                        dis_y = pb_dist(pos_y[i], pos_y[j], size_y);
                        r = sqrt(pow(dis_x,2)+pow(dis_y,2));
                        //Attraction-Repulsion Strength
                        if (i != j) {
                            if (r <= r1) {
                                if (r < r0) {
                                    //Infinite repulsion
                                    if (inf_count == 0) {
                                        f_x = 0;
                                        f_y = 0;
                                    }
                                    inf_count++;
                                    if (r > 0) {//Avoid dividing by zero
                                        f_x += -dis_x/r;
                                        f_y += -dis_y/r;
                                    }
                                } else {
                                    //Equilibrium attraction and repulsion
                                    if (inf_count == 0){
                                        temp = -f0 + (r-r0)/(r1-r0)*(1.+beta[ctype*3+cellType(j, cutoff)])*f0;
                                        f_x += temp*(dis_x)/r;
                                        f_y += temp*(dis_y)/r;
                                    }
                                }
                            }
                        }
                        //Alignment Strength
                        if (r <= rv) {
                            temp = sqrt(pow(v_x[j],2) + pow(v_y[j],2));
                            if (temp > 0) {
                                avgdir_x += v_x[j]/temp;
                                avgdir_y += v_y[j]/temp;
                            }
                        }
                    }
        
                    // ANGULAR INERTIA
                    v_x[i] *= inert;
                    v_y[i] *= inert;
        
                    // INTERACTION
                    if (inf_count > 0) {
                        f_x = f_x/inf_count*10000;
                        f_y = f_y/inf_count*10000;
                    }
                    v_x[i] += f_x;
                    v_y[i] += f_y;
        
                    // ALIGNMENT
                    temp = sqrt(pow(avgdir_x,2) + pow(avgdir_y,2));
                    if (temp > 0) {//Avoid dividing by zero
                        avgdir_x /= temp;
                        avgdir_y /= temp;
                    }
                    v_x[i] += fa * avgdir_x;
                    v_y[i] += fa * avgdir_y;
        
                    //GRADIENT
                    v_x[i] += grad_x[ctype];
                    v_y[i] += grad_y[ctype];
        
                    //NORMALIZE into unit vector (contain angle info)
                    temp = sqrt(pow(v_x[i],2) + pow(v_y[i],2));
                    if (temp > 0) {//Avoid dividing by zero
                        v_x[i] /= temp;
                        v_y[i] /= temp;
                    }
        
                    //NOISE
                    noise = nint*M_PI*((static_cast <float> (rand()) / static_cast <float> (RAND_MAX))*2-1);
                    c = cos(noise);
                    s = sin(noise);
                    temp = v_x[i];
                    v_x[i] = v0[ctype]*(v_x[i]*c - v_y[i]*s);
                    v_y[i] = v0[ctype]*(temp*s + v_y[i]*c);
                }
            }
        
            for (i = 0; i < n; i++)
            {
                ctype = cellType(i, cutoff);
                if (pinned[ctype] == 0) {
                    //WITHIN BOUNDARY
                    pos_x[i] += v_x[i];
                    pos_x[i] = pb_fitInto(pos_x[i], size_x);
                    pos_y[i] += v_y[i];
                    pos_y[i] = pb_fitInto(pos_y[i], size_y);
                }
            }
        
        
        
        if(py_local_dict)                                  
        {                                                  
            py::dict local_dict = py::dict(py_local_dict); 
        }                                                  
    
    }                                
    catch(...)                       
    {                                
        return_val =  py::object();      
        exception_occurred = 1;       
    }                                
    /*cleanup code*/                     
    if(v0_used)
    {
        Py_XDECREF(py_v0);
        #undef V01
        #undef V02
        #undef V03
        #undef V04
    }
    if(pinned_used)
    {
        Py_XDECREF(py_pinned);
        #undef PINNED1
        #undef PINNED2
        #undef PINNED3
        #undef PINNED4
    }
    if(cutoff_used)
    {
        Py_XDECREF(py_cutoff);
        #undef CUTOFF1
        #undef CUTOFF2
        #undef CUTOFF3
        #undef CUTOFF4
    }
    if(beta_used)
    {
        Py_XDECREF(py_beta);
        #undef BETA1
        #undef BETA2
        #undef BETA3
        #undef BETA4
    }
    if(grad_x_used)
    {
        Py_XDECREF(py_grad_x);
        #undef GRAD_X1
        #undef GRAD_X2
        #undef GRAD_X3
        #undef GRAD_X4
    }
    if(grad_y_used)
    {
        Py_XDECREF(py_grad_y);
        #undef GRAD_Y1
        #undef GRAD_Y2
        #undef GRAD_Y3
        #undef GRAD_Y4
    }
    if(pos_x_used)
    {
        Py_XDECREF(py_pos_x);
        #undef POS_X1
        #undef POS_X2
        #undef POS_X3
        #undef POS_X4
    }
    if(pos_y_used)
    {
        Py_XDECREF(py_pos_y);
        #undef POS_Y1
        #undef POS_Y2
        #undef POS_Y3
        #undef POS_Y4
    }
    if(v_x_used)
    {
        Py_XDECREF(py_v_x);
        #undef V_X1
        #undef V_X2
        #undef V_X3
        #undef V_X4
    }
    if(v_y_used)
    {
        Py_XDECREF(py_v_y);
        #undef V_Y1
        #undef V_Y2
        #undef V_Y3
        #undef V_Y4
    }
    if(!(PyObject*)return_val && !exception_occurred)
    {
                                  
        return_val = Py_None;            
    }
                                  
    return return_val.disown();           
}                                


static PyMethodDef compiled_methods[] = 
{
    {"fb_tick",(PyCFunction)fb_tick , METH_VARARGS|METH_KEYWORDS},
    {"pb_tick",(PyCFunction)pb_tick , METH_VARARGS|METH_KEYWORDS},
    {NULL,      NULL}        /* Sentinel */
};

PyMODINIT_FUNC initc_code(void)
{
    
    Py_Initialize();
    import_array();
    PyImport_ImportModule("numpy");
    (void) Py_InitModule("c_code", compiled_methods);
}

#ifdef __CPLUSCPLUS__
}
#endif
