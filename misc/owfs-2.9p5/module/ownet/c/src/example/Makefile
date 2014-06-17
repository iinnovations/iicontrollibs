# Makefile for ownet example program -- invoked separately from this directory
# $Id$

CFLAGS = -g -I/opt/owfs/include

EXAMPLEA = ownetexample
EXAMPLEA_OBJS = ownetexample.o
EXAMPLEB = ownet_tree
EXAMPLEB_OBJS = ownet_tree.o
EXAMPLEC = ownet_rep_test
EXAMPLEC_OBJS = ownet_rep_test.o
EXAMPLED = ownet_init_test
EXAMPLED_OBJS = ownet_init_test.o

all:	$(EXAMPLEA) $(EXAMPLEB) $(EXAMPLEC) $(EXAMPLED)

ifeq "$(shell uname)" "Darwin"

# Compile-flags for MacOSX
DARWINLDFLAGS = -L/opt/owfs/lib -lownet -low -L/usr/lib/x86_64-linux-gnu -lusb

$(EXAMPLEA): $(EXAMPLEA_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLEA_OBJS) $(DARWINLDFLAGS)

$(EXAMPLEB): $(EXAMPLEB_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLEB_OBJS) $(DARWINLDFLAGS)

$(EXAMPLEC): $(EXAMPLEC_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLEC_OBJS) $(DARWINLDFLAGS)

$(EXAMPLED): $(EXAMPLED_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLED_OBJS) $(DARWINLDFLAGS)

else

# Compile-flags for Linux and Cygwin
LDFLAGS = -L/opt/owfs/lib -Wl,--rpath -Wl,/opt/owfs/lib -lownet

$(EXAMPLEA): $(EXAMPLEA_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLEA_OBJS) $(LDFLAGS)

$(EXAMPLEB): $(EXAMPLEB_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLEB_OBJS) $(LDFLAGS)

$(EXAMPLEC): $(EXAMPLEC_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLEC_OBJS) $(LDFLAGS)

$(EXAMPLED): $(EXAMPLED_OBJS)
	gcc $(CFLAGS) -o $@ $(EXAMPLED_OBJS) $(LDFLAGS)

endif

%.o: %.c
	gcc $(CFLAGS) -c -o $@ $<

clean:
	$(RM) -f $(EXAMPLEA) $(EXAMPLEB) $(EXAMPLEC) $(EXAMPLED) *.o *~ .~ Makefile
